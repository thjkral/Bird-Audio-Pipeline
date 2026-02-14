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
from utils.database_connector import DatabaseConnector

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

    args = arguments.parse_args()

    logging.info(f'PIPELINE STARTED\n'
                 f'\t\tStarted at= {datetime.now()}\n'
                 f'\t\tLoading audio= {args.load_audio}')

    database_connection = DatabaseConnector(os.getenv('DATABASE_USER'), os.getenv('DATABASE_PASSWORD'), 'AuditoryMonitoring')

    if args.load_audio:
        logging.info('Starting to load audio files')
        load_audio.start_load(os.getenv('DATA_ROOT_LOCATION'), database_connection)

    database_connection.close_connection()
