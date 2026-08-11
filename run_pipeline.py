"""
Run all the processes of the pipeline in the correct order
"""

import argparse
import dotenv
import logging
import sys
import os
import subprocess

from datetime import datetime
from audio_intake import load_audio
from clean_and_validate import clean_audio
from reports import make_reports
from database import Engine, DatabaseMaintenance


BIRDNET_BATCH_SIZE = 250

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
    arguments.add_argument('-a', '--all', action='store_true', help='Run all processes')
    arguments.add_argument('-l', '--load_audio', action='store_true', help='Load audio')
    arguments.add_argument('-d', '--date', action='store', help='Date to load from. Keep empty to load all')
    arguments.add_argument('-c', '--clean_audio', action='store_true', help='Clean the imported recordings')
    arguments.add_argument('-v', '--validate_audio', action='store_true', help='Validate audio recording')
    arguments.add_argument('-x', '--acoustics', action='store_true', help='Detect bird song')
    arguments.add_argument(
        '--birdnet-batch-size',
        type=int,
        default=BIRDNET_BATCH_SIZE,
        help='Number of recordings processed by each isolated BirdNET worker',
    )
    arguments.add_argument('-r', '--reports', action='store_true', help='Create report tables. Current reports will be overwritten')

    args = arguments.parse_args()
    if args.birdnet_batch_size <= 0:
        arguments.error('--birdnet-batch-size must be greater than zero')

    logging.info(f'PIPELINE STARTED\n'
                 f'\t\tStarted at= {datetime.now()}\n'
                 f'\t\tLoading audio= {args.load_audio}\n'
                 f'\t\tCleaning audio= {args.clean_audio}\n'
                 f'\t\tValidating audio= {args.validate_audio}\n'
                 f'\t\tAcoustics= {args.acoustics}')

    db_credentials = _get_db_credentials_dict()

    db_engine = Engine(db_credentials)

    database_maintenance = DatabaseMaintenance(db_engine.engine)
    database_maintenance.create_tables_if_not_exist()


    curr_batch_id = db_engine.get_latest_batch_id()

    if args.load_audio or args.all:
        logging.info('Starting to load audio files')
        load_audio.start_load(os.getenv('DATA_ROOT_LOCATION'), db_engine.engine, curr_batch_id+1)

    if args.clean_audio or args.all:
        logging.info('CLEANING AUDIO')
        if args.all:
            curr_batch_id += 1
        clean_audio.start_clean(db_engine.engine, curr_batch_id)

    #TODO: add validation steps here

    if args.acoustics or args.all:
        logging.info('ACOUSTICS')
        while True:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "acoustics.birdnet_worker",
                    "--batch-size", str(args.birdnet_batch_size),
                ],
                check=False,
            )

            if result.returncode == 0:
                logging.info('BirdNET worker completed a batch; starting the next worker.')
                continue
            if result.returncode == 1:
                logging.info('BirdNET detection is complete; no recordings remain.')
                break
            if result.returncode == 2:
                logging.warning(
                    'BirdNET worker reached its file descriptor limit; starting a fresh worker.'
                )
                continue
            if result.returncode == 3:
                logging.critical('BirdNET worker stopped due to a database error.')
                raise RuntimeError('BirdNET detection stopped due to a database error')
            if result.returncode == 4:
                logging.error('BirdNET worker stopped due to an unexpected error.')
                raise RuntimeError('BirdNET detection stopped due to an unexpected error')

            logging.error('BirdNET worker exited with unknown code %s.', result.returncode)
            raise RuntimeError(
                f'BirdNET detection stopped with unknown worker exit code {result.returncode}'
            )


    if args.reports or args.all:
        logging.info('REPORTING')
        make_reports.generate_reports(db_engine.engine)


