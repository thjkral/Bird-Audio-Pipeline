"""
Go over the filesystem, detect new audio, extract data and store in database
"""

import os
import logging
import shutil

from .Recording import Recording


def start_load(root_dir, db_conn):
    '''
    Loops over all audio files in a given directory, creates objects and saves them to the database.
    :param root_dir: Root folder where all data is stored
    :return:
    '''
    logging.info(f'Looking for data at location: {root_dir}')
    recordings_list = []
    for file in os.listdir(root_dir):  # generate Recording objects for each audiofile
        filename = os.fsdecode(file)
        if filename.endswith('.wav'):
            full_path = os.path.join(root_dir, filename)
            recording = Recording(full_path, filename)
            recordings_list.append(recording)

    logging.info(f'Processed {len(recordings_list)} audio files')

    for rec in recordings_list:  # copy each record to a new location with a directory tree based on the recording date
        rec.set_new_filepath(os.getenv('STORE_LOCATION'))
        try:
            os.makedirs(os.path.dirname(rec.new_file_path), exist_ok=True)
            shutil.copyfile(rec.old_file_path, rec.new_file_path)
        except Exception as err:
            logging.error(f'Problem while copying file {rec.old_file_path} to {rec.new_file_path}:\n{err}')
    logging.info('Copied audio files to new location')

    #TODO: save info to database
