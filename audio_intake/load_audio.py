"""
Go over the filesystem, detect new audio, extract data and store in database
"""

import os
import logging
import shutil
from .Recording import Recording


def _copy_recording_file(recording):
    try:
        pass
    except Exception as err:
        logging.error(f'Problem while copying file {recording.old_file_path} to {recording.new_file_path}:\n{err}')


def start_load(root_dir, db_conn):
    '''
    Loops over all audio files in a given directory, creates objects and saves them to the database.
    :param: Root folder where all data is stored
    '''
    logging.info(f'Looking for data at location: {root_dir}')
    recordings_list = []
    for file in os.listdir(root_dir):  # generate Recording objects for each audiofile
        filename = os.fsdecode(file)
        if filename.endswith('.wav'):
            full_path = os.path.join(root_dir, filename)
            recording = Recording(full_path, filename)
            recordings_list.append(recording)

    new_file_count = len(recordings_list)
    logging.info(f'Identified {new_file_count} new audio files to process. Starting load sequence...')

    rows_in_db_before = db_conn.get_number_of_rows('Recording')

    for rec in recordings_list:  # copy each record to a new location with a directory tree based on the recording date
        rec.set_new_filepath(os.getenv('STORE_LOCATION'))
        try:
            os.makedirs(os.path.dirname(rec.new_file_path), exist_ok=True)
            shutil.copyfile(rec.old_file_path, rec.new_file_path)
            logging.info(f'Copied audio file {rec.filename} to new location')

            logging.info(f'Adding recording {rec.filename} to database')
            db_conn.insert_recording(rec)
        except Exception as err:
            logging.error(f'Problem while copying file {rec.old_file_path} to {rec.new_file_path}:\n{err}')

    rows_in_db_after = db_conn.get_number_of_rows('Recording')
    rows_added = rows_in_db_after - rows_in_db_before
    if rows_added == new_file_count:
        logging.info('All new recordings added to the database.')
    elif rows_added == 0:
        logging.warning('Added no new recordings to the database!')
    elif rows_added < new_file_count and rows_added != 0:
        logging.warning(f'New recordings partially loaded. Found {new_file_count - rows_added} possible duplicates.')
