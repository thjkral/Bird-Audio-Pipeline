import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import insert, select
from database.tables import (
    Recording_cleaned,
    Recording_final,
    TransformationProcessedRecordings,
)
import pandas as pd


def adjust_for_dst(timestamp: datetime) -> datetime:
    """
    Adjust a microphone timestamp from fixed Dutch summer-time clock
    to Dutch local civil time.

    If the date falls within Dutch daylight saving time, the timestamp
    is returned unchanged.

    If the date falls outside Dutch daylight saving time, one hour is
    subtracted.

    Parameters
    ----------
    timestamp : datetime
        Naive datetime as recorded by the microphone.

    Returns
    -------
    datetime
        Original timestamp during DST, otherwise timestamp minus one hour.
    """

    timezone = ZoneInfo("Europe/Amsterdam")

    # Use noon on the same date to determine whether that date is in DST.
    # This avoids the DST transition itself causing ambiguity.
    reference = datetime.combine(timestamp.date(), time(12))
    reference = reference.replace(tzinfo=timezone)

    is_dst = reference.dst() != timedelta(0)

    if is_dst:
        return timestamp

    return timestamp - timedelta(hours=1)


def _fetch_recordings(db_engine):
    stmt = (
        select(Recording_cleaned)
        .outerjoin(
            TransformationProcessedRecordings,
            TransformationProcessedRecordings.c.recording_id == Recording_cleaned.c.id
        )
        .where(TransformationProcessedRecordings.c.recording_id.is_(None))
    )
    try:
        with db_engine.connect() as conn:
            result = conn.execute(stmt)

            # Convert to DataFrame safely
            df = pd.DataFrame(result.mappings().all())
            return df

    except Exception as err:
        logging.error(f'Cannot fetch dataframe for validating data:\n{err}')
        return pd.DataFrame()


def persist_final_recordings_and_mark_processed(db_engine, dataframe):
    """Insert transformed recordings and mark their source rows as processed.

    Both writes run in one transaction so a recording cannot be marked as
    transformed unless its corresponding ``Recording_final`` row was stored.
    ``_fetch_recordings`` provides the source identifier as ``id``; a
    ``recording_id`` column is also accepted for callers that already expose
    that name.
    """
    if dataframe.empty:
        return

    final_columns = [
        column.name for column in Recording_final.columns if column.name in dataframe.columns
    ]
    if not final_columns:
        raise ValueError('Cannot insert final recordings: no Recording_final columns in DataFrame')

    recording_id_column = 'recording_id' if 'recording_id' in dataframe.columns else 'id'
    if recording_id_column not in dataframe.columns:
        raise ValueError('Cannot mark recordings as processed: DataFrame has no recording_id or id column')

    with db_engine.begin() as conn:
        conn.execute(
            insert(Recording_final),
            dataframe.loc[:, final_columns].to_dict(orient='records'),
        )
        conn.execute(
            insert(TransformationProcessedRecordings),
            [
                {'recording_id': recording_id}
                for recording_id in dataframe[recording_id_column]
            ],
        )


def start(db_engine):

    logging.info('Adjusting timestamps for Daylight saving time')

    dataframe = _fetch_recordings(db_engine)
    if dataframe.empty:
        logging.info('No recordings available for DST')
    else:
        logging.info(f'Adjusting {len(dataframe)} timestamps for DST')
        dataframe['timestamp_DST_adjusted'] = dataframe['timestamp'].apply(adjust_for_dst)
        persist_final_recordings_and_mark_processed(db_engine, dataframe)
