import logging
from datetime import datetime
import pandas as pd

from database import CleaningService


def _check_null_values(dataframe, db, field_list=None):
    df_clean = dataframe.dropna(axis=0,
                                how='any',
                                subset=field_list)

    df_nans = dataframe[~dataframe.index.isin(df_clean.index)]
    _append_to_log_table(df_nans, 'null', db)

    return df_clean

def _check_recording_duration(dataframe, db_conn):
    """
    Check if the duration length is within range
    :param dataframe: dataframe of recordings
    :param db_conn: connection to database
    :return: cleaned dataframe
    """
    min_duration = 60
    max_duration = 600

    valid_mask = dataframe["duration"].between(min_duration, max_duration)

    clean_df = dataframe[valid_mask].copy()
    outside_range_df = dataframe[~valid_mask].copy()

    _append_to_log_table(outside_range_df, "outside_range", db_conn)
    return clean_df


def _check_duplicates_batch(dataframe, db_conn):
    """
    Check if duplicates are present in the same dataframe. This indicates duplicate files within the same batch.
    :param dataframe: dataframe of recordings
    :param db_conn: connection to database
    :return: cleaned dataframe
    """
    dataframe['is_duplicate'] = dataframe.duplicated(keep='first')

    clean_df = dataframe[~dataframe['is_duplicate']].copy()
    duplicates_df = dataframe[dataframe['is_duplicate']].copy()

    _append_to_log_table(duplicates_df, 'duplicate_batch', db_conn)
    return clean_df


def _check_duplicates_historical(dataframe, db_conn):
    """
    Check if the dataframe contains recording already in the dataset. This indicates a recording loaded into the data
    with an earlier run.
    :param dataframe: dataframe of recordings
    :param db_conn: connection to database
    :return: cleaned dataframe
    """
    unique_file_hashes = db_conn.get_unique_historic_hashes()
    if not unique_file_hashes.empty:
        existing_set = set(unique_file_hashes["file_hash"])
        mask = dataframe["file_hash"].isin(existing_set)

        unique_rows = dataframe[~mask].copy()
        duplicate_rows = dataframe[mask].copy()

        _append_to_log_table(duplicate_rows, 'duplicate_historical', db_conn)
        return unique_rows
    else:
        logging.info('No historical recordings found for cleaning. If this is not the first time running the pipeline, '
                     'this can be an error')
        return dataframe


def _append_to_log_table(dataframe, reject_type, db_conn):
    """
    Append rejected recordings to the log table with the reason for rejection
    :param dataframe: dataframe with rejected recordings
    :param reject_type: reason for rejecting the recordings
    :param db_conn: connection to database
    """
    if reject_type == 'null':
        dataframe['is_null'] = True
        db_conn.insert_rejected_recordings(dataframe)
    if reject_type == 'duplicate_batch':
        dataframe["is_duplicate"] = True
        dataframe["duplicate_type"] = 'batch'
        db_conn.insert_rejected_recordings(dataframe)
    if reject_type == 'duplicate_historical':
        dataframe["is_duplicate"] = True
        dataframe["duplicate_type"] = 'historical'
        db_conn.insert_rejected_recordings(dataframe)
    if reject_type == 'outside_range':
        dataframe["outside_range"] = True
        db_conn.insert_rejected_recordings(dataframe)


def start_clean(db_engine, batch_id):
    """
    Clean the staged recordings by running various checks. Accepted recordings are stored in the `Recording_cleaned`
    table, while rejected recordings are stored in the `Recording_rejected` table.
    """
    logging.info(f'Cleaning data with batch ID: {batch_id}')

    clean_service = CleaningService(db_engine)

    batch_df = clean_service.get_recordings_for_cleaning(batch_id)

    if not batch_df.empty or batch_df is not None:
        batch_df.drop('ingestion_at', axis=1, inplace=True)

        rows_in_batch = len(batch_df)
        logging.info(f'Number of recordings in batch: {len(batch_df)}')

        # Identify rows with missing values
        no_nulls_df = _check_null_values(batch_df, clean_service)
        nulls_in_batch = len(no_nulls_df)
        logging.info(f'Number of null values in batch: {rows_in_batch - nulls_in_batch}')

        # Identify recording with a duration length out of range
        outside_range_df = _check_recording_duration(batch_df, clean_service)
        outside_range_in_batch = len(outside_range_df)
        logging.info(f'Number of recordings with out of range duration: {nulls_in_batch - outside_range_in_batch}')

        # Identify duplicate rows within the batch
        no_batch_dups_df = _check_duplicates_batch(outside_range_df, clean_service)
        dups_in_batch = len(no_batch_dups_df)
        logging.info(f'Number of duplicates in batch: {outside_range_in_batch - dups_in_batch}')

        # Identify duplicate rows within the historic data
        no_historic_dups_df = _check_duplicates_historical(no_batch_dups_df, clean_service)
        dups_in_history = len(no_historic_dups_df)
        logging.info(f'Number of duplicates in history: {dups_in_batch - dups_in_history}')

        logging.info(f'Cleaning finished! Out of {rows_in_batch} recordings, {dups_in_history} passed')
        clean_service.insert_cleaned_recordings(no_historic_dups_df)

    else:
        logging.info('No recordings found for cleaning')
