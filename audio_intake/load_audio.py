"""
Go over the filesystem, detect new audio, extract data and store in database
"""

import os
import logging
from datetime import datetime
from tinytag import TinyTag
from .Recording import Recording


def start_load(root_dir):
    '''
    Loops over all audio files in a given directory, creates objects and saves them to the database.
    :param root_dir:
    :return:
    '''
    logging.info(f'Looking for data at location: {root_dir}')
    for file in os.listdir(root_dir):
        filename = os.fsdecode(file)
        if filename.endswith('.wav'):
            full_path = os.path.join(root_dir, filename)

            recording = Recording(full_path, filename)
            logging.info(recording)

            #TODO: save info to database
