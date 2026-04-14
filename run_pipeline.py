"""
Run all the processes of the pipeline in the correct order
"""

import argparse
import dotenv
import logging
import sys
import os

from datetime import datetime
from audio_intake import load_audio
from clean_and_validate import clean_audio, validate_audio
from database.MaintenanceService import DatabaseMaintenance
from utils.database_connector import DatabaseConnector

def _get_db_credentials_dict():
    db_credentials_dict = {'user': os.getenv('DATABASE_USER'),
                           'password': os.getenv('DATABASE_PASSWORD'),
                           'database': os.getenv('DATABASE_NAME')}
    return db_credentials_dict

if __name__ == '__main__':

    # Open and load the config
    try:
        dotenv.load_dotenv('/etc/bird_audio_pipeline.conf')
    except FileNotFoundError:
        print("ERROR: Can't find config file")
        sys.exit(0)

    # Set up logging
    logfile = os.getenv('LOG_FILE_DIR') + str(datetime.now().strftime("%d-%m-%Y")) + '.log'
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s | %(levelname)s | %(message)s',
                        datefmt='%H:%M:%S',
                        handlers=[
                            logging.FileHandler(logfile),
                            logging.StreamHandler(sys.stdout)
                        ])

    arguments = argparse.ArgumentParser(description='Pipeline for processing ecological monitoring of birds')
    arguments.add_argument('-l', '--load_audio', action='store_true', help='Load audio')
    arguments.add_argument('-d', '--date', action='store', help='Date to load from. Keep empty to load all')
    arguments.add_argument('-c', '--clean_audio', action='store_true', help='Clean the imported recordings')
    arguments.add_argument('-v', '--validate_audio', action='store_true', help='Validate audio recording')

    args = arguments.parse_args()

    logging.info(f'PIPELINE STARTED\n'
                 f'\t\tStarted at= {datetime.now()}\n'
                 f'\t\tLoading audio= {args.load_audio}\n'
                 f'\t\tCleaning audio= {args.clean_audio}\n'
                 f'\t\tValidating audio= {args.validate_audio}')

    database_connection = DatabaseConnector(os.getenv('DATABASE_USER'), os.getenv('DATABASE_PASSWORD'), os.getenv('DATABASE_NAME'))
    db_credentials = _get_db_credentials_dict()

    database_maintenance = DatabaseMaintenance(db_credentials)
    database_maintenance.create_tables_if_not_exist()


    curr_batch_id = database_connection.get_latest_batch_id()

    if args.load_audio:
        logging.info('Starting to load audio files')
        load_audio.start_load(os.getenv('DATA_ROOT_LOCATION'), database_connection, curr_batch_id+1)

    if args.clean_audio:
        logging.info('CLEANING AUDIO')
        clean_audio.start_clean(db_credentials, curr_batch_id)

    if args.validate_audio:
        logging.info('VALIDATING AUDIO')
        validate_audio.validate(database_connection)
