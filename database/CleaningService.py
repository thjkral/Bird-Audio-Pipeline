from database.Engine import Engine
import logging
import pandas as pd
from sqlalchemy import insert

from database.tables import Recording_cleaned

class CleaningService(Engine):
    def __init__(self, db_credentials):
        super().__init__(db_credentials)

    def insert_rejected_recordings(self, dataframe):
        try:
            with self.engine.connect() as conn:
                dataframe.to_sql(
                    name="Recording_rejected",
                    con=conn,
                    if_exists="append",  # VERY important
                    index=False,
                    method="multi",  # performance boost
                    chunksize=1000  # avoids memory / transaction issues
                )
        except Exception as err:
            logging.error(f'Cannot insert rejected recordings:\n{err}')


    def get_unique_historic_hashes(self):
        try:
            existing_keys = pd.read_sql(
                "SELECT file_hash FROM Recording_cleaned",
                self.engine
            )
            return existing_keys
        except Exception as err:
            logging.error(f'Cannot get unique historic hashes:\n{err}')
            return None


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