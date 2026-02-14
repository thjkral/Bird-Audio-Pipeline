"""
Connect to the database and perform tasks
"""
import logging
from sqlalchemy import create_engine


class DatabaseConnector:
    """
    Connector to the database
    """

    def __init__(self, user, password, database):
        self.user = user
        self.password = password
        self.database = database
        self.db_connection = self._generate_connection()

    def __str__(self):
        return f'User= {self.user}, Database= {self.database}'

    def _generate_connection(self):
        """
        Try to connect to the database and establish a connection
        :return: Database connector object
        """
        try:
            connection_string = "mysql+pymysql://{}:{}@localhost/{}?charset=utf8mb4".format(self.user,
                                                                                            self.password,
                                                                                            self.database)
            logging.info('Connected to database')
            engine = create_engine(connection_string, isolation_level="AUTOCOMMIT")
            return engine.connect()
        except Exception as err:
            logging.critical(f'Cannot connect to database:\n{err}')
            exit(0)

    def close_connection(self):
        try:
            self.db_connection.close()
            logging.info('Closed the database connection')
        except Exception as err:
            logging.error(f'Cannot close the database connection:\n{err}')

    def insert_recording(self):
        query_text = f"""
                        INSERT INTO 
                        """
