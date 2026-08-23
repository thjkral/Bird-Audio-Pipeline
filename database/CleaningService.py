import logging
import pandas as pd
from sqlalchemy import insert, select

from database.tables import Recording_cleaned, Recording_staging, Recording_rejected
from corvium_core.database.tables import Media

class CleaningService():
    def __init__(self, engine):
        self.engine = engine


    def get_recordings_for_cleaning(self, batch_id):
        """
        Returns a pandas DataFrame of recordings for a given batch_id
        """
        stmt = (
            select(Recording_staging)
            .where(Recording_staging.c.batch_id == batch_id)
        )

        try:
            with self.engine.connect() as conn:
                result = conn.execute(stmt)

                # Convert to DataFrame safely
                df = pd.DataFrame(result.mappings().all())
                return df

        except Exception as err:
            logging.error(f'Cannot fetch dataframe for batch {batch_id}:\n{err}')
            return pd.DataFrame()


    def insert_rejected_recordings(self, df, batch_size=1000):
        """
        Inserts rejected records using SQLAlchemy Core (no to_sql).
        """
        if df.empty:
            return

        stmt = insert(Recording_rejected)

        try:
            with self.engine.begin() as conn:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i + batch_size]

                    conn.execute(
                        stmt,
                        batch.to_dict(orient="records")
                    )

        except Exception as err:
            logging.error(f'Cannot insert rejected recordings:\n{err}')


    def get_unique_historic_hashes(self):
        """
        Returns a DataFrame of existing file_hash values.
        """
        stmt = select(Recording_cleaned.c.file_hash)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(stmt)
                df = pd.DataFrame(result.mappings().all())
                return df

        except Exception as err:
            logging.error(f'Cannot get unique historic hashes:\n{err}')
            return pd.DataFrame()

    def insert_cleaned_recordings(self, df, batch_size=1000):
        """
        Inserts accepted recordings into both Recording_cleaned and Media.

        Recording_cleaned contains the recording metadata.
        Media contains the physical file reference.
        """

        if df.empty:
            return

        recording_stmt = insert(Recording_cleaned)
        media_stmt = insert(Media)

        recording_columns = [
            "id",
            "file_name",
            "microphone_id",
            "rec_date",
            "start_time",
            "stop_time",
            "timestamp",
            "duration",
            "file_size",
            "samplerate",
            "channels",
            "bitdepth",
            "file_hash",
        ]

        media_columns = [
            "media_id",
            "media_type",
            "relative_filepath",
        ]

        with self.engine.begin() as conn:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]

                recordings = (
                    batch[recording_columns]
                    .to_dict(orient="records")
                )

                media = (
                    batch[["id", "relative_file_path"]]
                    .rename(
                        columns={
                            "id": "media_id",
                            "relative_file_path": "relative_filepath",
                        }
                    )
                    .assign(media_type="birdsong")
                    [media_columns]
                    .to_dict(orient="records")
                )

                conn.execute(media_stmt, media)
                conn.execute(recording_stmt, recordings)
