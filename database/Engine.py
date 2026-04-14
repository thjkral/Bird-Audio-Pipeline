"""
Connect to the database and perform tasks
"""
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from database.tables import Recording_cleaned

class Engine:
    """
    Connector to the database using SQLAlchemy sessions
    """

    def __init__(self, db_credentials):
        self.user = db_credentials.get('user')
        self.password = db_credentials.get('password')
        self.database = db_credentials.get('database')
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
            logging.info(f'Database: {__name__} created successfully')
            return engine
        except Exception as err:
            logging.critical(f'Cannot create engine:\n{err}')
            exit(0)


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

