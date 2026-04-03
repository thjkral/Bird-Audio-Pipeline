"""
Connect to the database and perform tasks
"""
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError


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

    def insert_staging_recording(self, recording_object, batch_id):
        '''
        Takes a Recording object and inserts in into the staging table. When a duplicate (ID based) is found, the row is
        ignored.
        :param recording_object: Object holding all necessary information for one row.
        '''
        query_text = f"""
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
                            batch_id)
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
                        {recording_object.bitdepth},
                        '{recording_object.file_hash}',
                        {batch_id})
                        ;
                        """
        try:
            with self.db_connection.begin():
                self.db_connection.execute(query_text)
            return 'Succes'
        except Exception as err:
            logging.error(
                f'Cannot add a row for the audio file named <{recording_object.filename}> to the Recording table:\n{err}')
            return None

    def _add_duplicate(self, recording_object):
        duplicate_query = f"""
                            INSERT INTO Recording_duplicates(
                            id,
                            file_name,
                            rec_date,
                            start_time,
                            stop_time,
                            file_hash)
                            VALUES(
                            '{recording_object.rec_id}',
                            '{recording_object.filename}',
                            '{recording_object.rec_date}',
                            '{recording_object.start_time}',
                            '{recording_object.stop_time}',
                            '{recording_object.file_hash}'
                            );
                           """
        try:
            with self.db_connection.begin():
                self.db_connection.execute(duplicate_query)
        except Exception as err:
            logging.error(f'Cannot add recording <{recording_object.filename}> as a duplicate:\n{err}')

    def get_latest_batch_id(self):
        batch_id_query = f'SELECT DISTINCT batch_id FROM Recording_staging ORDER BY batch_id DESC LIMIT 1'
        highest_id = self.db_connection.execute(batch_id_query).fetchone()
        if highest_id:
            return int(highest_id[0])
        else:
            return 0

    def get_recordings_for_cleaning(self, batch_id):
        try:
            recordings_query = f"SELECT * FROM Recording_staging WHERE batch_id = {batch_id};"
            return pd.read_sql(recordings_query, self.db_connection)
        except Exception as err:
            logging.error(f'Cannot fetch dataframe for cleaning from database!:\n{err}')
