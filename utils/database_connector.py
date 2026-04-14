"""
Connect to the database and perform tasks
"""
import logging
import pandas as pd
from sqlalchemy import create_engine, text, insert

from database.tables.Recording_cleaned import Recording_cleaned
from sqlalchemy.orm import Session

class DatabaseConnector:
    """
    Connector to the database using SQLAlchemy sessions
    """

    def __init__(self, user, password, database):
        self.user = user
        self.password = password
        self.database = database
        self.engine = self._generate_engine()

    def __str__(self):
        return f'User= {self.user}, Database= {self.database}'

    def _generate_engine(self):
        """
        Create a SQLAlchemy engine.
        """
        try:
            connection_string = f"mysql+pymysql://{self.user}:{self.password}@localhost/{self.database}?charset=utf8mb4"
            engine = create_engine(connection_string, future=True)
            logging.info('Engine created successfully')
            return engine
        except Exception as err:
            logging.critical(f'Cannot create engine:\n{err}')
            exit(0)

    def insert_staging_recording(self, recording_object, batch_id):
        """
        Inserts a recording into Recording_staging. Transaction-safe.
        """
        query_text = text(f"""
            INSERT INTO Recording_staging(
                id,
                file_name,
                microphone_id,
                rec_date,
                start_time,
                stop_time,
                duration,
                file_path,
                file_size,
                samplerate,
                channels,
                bitdepth,
                file_hash,
                batch_id
            ) VALUES (
                :id, :filename, :microphone_id, :rec_date, :start_time, :stop_time,
                :duration, :file_path, :file_size, :samplerate, :channels,
                :bitdepth, :file_hash, :batch_id
            )
        """)
        params = recording_object.to_db_params(batch_id)

        try:
            with Session(self.engine) as session:
                session.execute(query_text, params)
                session.commit()
            return "Success"
        except Exception as err:
            logging.error(f'Cannot add recording {recording_object.filename}:\n{err}')
            return None

    def get_latest_batch_id(self):
        """
        Fetches the highest batch_id from Recording_staging
        """
        batch_id_query = text("""
            SELECT DISTINCT batch_id
            FROM Recording_staging
            ORDER BY batch_id DESC
            LIMIT 1
        """)
        try:
            with Session(self.engine) as session:
                result = session.execute(batch_id_query).fetchone()
                return int(result[0]) if result else 0
        except Exception as err:
            logging.critical(f'Cannot fetch latest batch_id:\n{err}')

    def get_recordings_for_cleaning(self, batch_id):
        """
        Returns a pandas DataFrame of recordings for a given batch_id
        """
        recordings_query = text("""
                                SELECT *
                                FROM Recording_staging
                                WHERE batch_id = :batch_id
                                """)
        try:
            with self.engine.connect() as conn:
                return pd.read_sql_query(recordings_query, conn, params={"batch_id": batch_id})
        except Exception as err:
            logging.error(f'Cannot fetch dataframe for batch {batch_id}:\n{err}')
            return pd.DataFrame()

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