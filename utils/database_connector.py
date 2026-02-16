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
        '''
        Closes the connection to the database.
        '''
        try:
            self.db_connection.close()
            logging.info('Closed the database connection')
        except Exception as err:
            logging.error(f'Cannot close the database connection:\n{err}')

    def insert_recording(self, recording_object):
        '''
        Takes a Recording object and inserts in into the database. When a duplicate (ID based) is found, the row is
        ignored.
        :param recording_object: Object holding all necessary information for one row.
        '''
        query_text = f"""
                        INSERT IGNORE INTO Recording(
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
                            bitdepth)
                        VALUES(
                        '{recording_object.rec_id}',
                        '{recording_object.filename}',
                        '{recording_object.mic_id}',
                        '{recording_object.rec_date}',
                        '{recording_object.start_time}',
                        '{recording_object.stop_time}',
                        {recording_object.duration},
                        '{recording_object.new_file_path}',
                        {recording_object.filesize},
                        {recording_object.samplerate},
                        {recording_object.channels},
                        {recording_object.bitdepth})
                        ;
                        """
        try:
            self.db_connection.execute(query_text)
        except Exception as err:
            logging.error(f'Cannot add a row for the audio file named <{recording_object.filename}> to the Recording table:\n{err}')


    def get_number_of_rows(self, table_name):
        count_query = f'SELECT COUNT(*) FROM {table_name}'
        row_count = self.db_connection.execute(count_query).fetchone()
        return int(row_count[0])
