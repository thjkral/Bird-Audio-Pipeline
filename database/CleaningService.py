import logging
import pandas as pd
from sqlalchemy import insert, select

from database.tables import Recording_cleaned, Recording_staging, Recording_rejected

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
        Memory-efficient bulk insert into MariaDB using SQLAlchemy.

        Uses streaming via itertuples() to avoid large intermediate objects.
        """

        if df.empty:
            return

        stmt = insert(Recording_cleaned)

        # Convert column names once (faster access)
        columns = df.columns

        def row_to_dict(row):
            return dict(zip(columns, row))

        batch = []

        with self.engine.begin() as conn:
            for row in df.itertuples(index=False, name=None):

                batch.append(row_to_dict(row))

                if len(batch) >= batch_size:
                    conn.execute(stmt, batch)
                    batch.clear()

            # flush remaining rows
            if batch:
                conn.execute(stmt, batch)