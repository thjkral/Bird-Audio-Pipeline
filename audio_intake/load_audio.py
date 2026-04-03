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


def start_load(root_dir, db_conn, batch_id):
    '''
    Loops over all audio files in a given directory, creates objects and saves them to the database.
    :param: Root folder where all data is stored
    '''
    logging.info(f'Looking for data at location: {root_dir}.')
    recordings_list = []
    for file in os.listdir(root_dir):  # generate Recording objects for each audiofile
        filename = os.fsdecode(file)
        if filename.endswith('.wav'):
            full_path = os.path.join(root_dir, filename)
            recording = Recording(full_path, filename)
            recordings_list.append(recording)

    new_file_count = len(recordings_list)
    logging.info(f'Identified {new_file_count} new audio files to process. Starting load sequence with batch ID {batch_id}...')

    successful_inserts = 0
    errors = 0

    for rec in recordings_list:  # copy each record to a new location with a directory tree based on the recording date
        rec.set_new_filepath(os.getenv('STORE_LOCATION'))
        try:
            os.makedirs(os.path.dirname(rec.new_file_path), exist_ok=True)
            shutil.copyfile(rec.old_file_path, rec.new_file_path)
            logging.info(f'Copied audio file {rec.filename} to new location')

            logging.info(f'Adding recording {rec.filename} to database')
            result = db_conn.insert_staging_recording(rec, batch_id)

            if result == 'Succes':
                successful_inserts += 1
            elif result is None:
                errors += 1

        except Exception as err:
            logging.error(f'Problem while copying file {rec.old_file_path} to {rec.new_file_path}:\n{err}')

    logging.info(f'Finished loading to staging.\n'
                 f'\t{successful_inserts}/{new_file_count}: Successfull\n'
                 f'\t{errors}/{new_file_count}: Failed')

