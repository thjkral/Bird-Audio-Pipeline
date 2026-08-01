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
            logging.info(f'Engine created successfully')
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
            FROM audio_Recording_staging
            ORDER BY batch_id DESC
            LIMIT 1
        """)
        try:
            with Session(self.engine) as session:
                result = session.execute(batch_id_query).fetchone()
                return int(result[0]) if result else 0
        except Exception as err:
            logging.critical(f'Cannot fetch latest batch_id:\n{err}')



