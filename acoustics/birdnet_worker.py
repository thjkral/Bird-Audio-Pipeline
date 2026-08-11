import argparse
import errno
import logging
import os
import resource
import sys
from datetime import datetime

import dotenv
from sqlalchemy.exc import SQLAlchemyError

from .AcousticPrediction import AcousticPrediction
from database.DetectionService import DetectionService
from database.Engine import Engine
from .GeoPrediction import GeoPrediction


DEFAULT_BATCH_SIZE = 250
MODEL_VERSION = 2.4
FD_SAFETY_FRACTION = 0.80

EXIT_BATCH_COMPLETED = 0
EXIT_NO_RECORDINGS_REMAIN = 1
EXIT_FD_LIMIT_REACHED = 2
EXIT_DATABASE_ERROR = 3
EXIT_UNEXPECTED_ERROR = 4


def birdnet_week(dt):
    """
    Convert a datetime into BirdNET's 48-week numbering.
    """
    week_in_month = min((dt.day - 1) // 7 + 1, 4)
    return (dt.month - 1) * 4 + week_in_month


def _get_db_credentials_dict():
    return {
        'user': os.getenv('DATABASE_USER'),
        'password': os.getenv('DATABASE_PASSWORD'),
        'database': os.getenv('DATABASE_NAME'),
    }


def _configure_logging():
    """Configure worker logging when it is launched as a module."""
    if logging.getLogger().handlers:
        return

    handlers = [logging.StreamHandler(sys.stdout)]
    log_directory = os.getenv('LOG_FILE_DIR')
    if log_directory:
        logfile = os.path.join(
            log_directory,
            f"{datetime.now().strftime('%d-%m-%Y')}.log",
        )
        handlers.insert(0, logging.FileHandler(logfile))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S',
        handlers=handlers,
    )


def _fd_usage_and_threshold():
    """Return the current descriptor count and its conservative threshold."""
    soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    fd_count = len(os.listdir('/proc/self/fd'))
    if soft_limit == resource.RLIM_INFINITY:
        return fd_count, None, soft_limit
    return fd_count, max(1, int(soft_limit * FD_SAFETY_FRACTION)), soft_limit


def _fd_limit_reached():
    fd_count, threshold, soft_limit = _fd_usage_and_threshold()
    if threshold is None:
        logging.info('FD limit is unlimited; current FD usage: %s', fd_count)
        return False

    logging.debug(
        'FD limit: %s; current FD usage: %s; safety threshold: %s',
        soft_limit,
        fd_count,
        threshold,
    )
    return fd_count >= threshold


def run(batch_size):
    logging.info('Starting BirdNET worker; batch size: %s', batch_size)

    fd_count, threshold, soft_limit = _fd_usage_and_threshold()
    if threshold is None:
        logging.info('FD limit: unlimited; current FD usage: %s', fd_count)
    else:
        logging.info(
            'FD limit: %s; current FD usage: %s; safety threshold: %s',
            soft_limit,
            fd_count,
            threshold,
        )

    db_engine = Engine(_get_db_credentials_dict())
    detection_service = DetectionService(db_engine.engine)

    recordings = detection_service.get_unprocessed_recordings(batch_size)
    if recordings.empty:
        logging.info('No recordings remain for BirdNET detection.')
        return EXIT_NO_RECORDINGS_REMAIN

    logging.info('Retrieved %s recordings', len(recordings))

    logging.info('Setting up the birdnet models')
    import birdnet

    geo_model = birdnet.load("geo", "2.4", "tf", lang='nl')
    model = birdnet.load("acoustic", "2.4", "tf", lang='nl')

    recordings['week_number'] = recordings.apply(
        lambda row: birdnet_week(row['timestamp']),
        axis=1,
    )
    no_of_detections = 0
    processed_recordings = 0

    for week_number in recordings['week_number'].unique().tolist():
        mic_ids = recordings.loc[
            recordings['week_number'] == week_number, 'mic_id'
        ].unique().tolist()
        for mic_id in mic_ids:
            logging.info(
                'Retrieving recordings for week_number %s and mic_id %s',
                week_number,
                mic_id,
            )
            recordings_subset = recordings[
                (recordings['week_number'] == week_number)
                & (recordings['mic_id'] == mic_id)
            ]
            mic_location = detection_service.get_microphone_location(mic_id)
            geo_predictor = GeoPrediction(
                geo_model,
                mic_location.get('latitude'),
                mic_location.get('longitude'),
                week_number,
                0.01,
                detection_service,
            )
            geo_predictor.predict()

            for _, recording in recordings_subset.iterrows():
                if _fd_limit_reached():
                    logging.warning(
                        'File descriptor usage reached the safety threshold. '
                        'Processed %s recordings in this worker; exiting so a '
                        'fresh worker can continue.',
                        processed_recordings,
                    )
                    return EXIT_FD_LIMIT_REACHED

                logging.info(
                    'Processing recording %s (%s of %s)',
                    recording['file_id'],
                    processed_recordings + 1,
                    len(recordings),
                )
                acoustic_predictor = AcousticPrediction(
                    model,
                    recording['file_path'],
                    custom_species_list=geo_predictor.get_prediction_as_set(),
                    workers=8,
                    batch_size=16,
                    overlap_s=1.5,
                    model_version=MODEL_VERSION,
                )
                acoustic_predictor.predict()

                if acoustic_predictor.detection_df.empty:
                    logging.info('No detections for recording %s', recording['file_id'])
                    predictions_df = acoustic_predictor.detection_df
                else:
                    predictions_df = acoustic_predictor.transform_dataframe(
                        recording['file_id'],
                        geo_predictor,
                        week_number,
                    )
                    no_of_detections += len(predictions_df)

                detection_service.persist_detections_and_mark_processed(
                    predictions_df,
                    recording['file_id'],
                    MODEL_VERSION,
                )
                processed_recordings += 1

    logging.info(
        'BirdNET worker batch completed: %s recordings, %s detections.',
        processed_recordings,
        no_of_detections,
    )
    return EXIT_BATCH_COMPLETED


def main():
    parser = argparse.ArgumentParser(description='Process one isolated BirdNET batch.')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    if args.batch_size <= 0:
        parser.error('--batch-size must be greater than zero')

    dotenv.load_dotenv('/etc/bird_audio_pipeline.conf')

    try:
        _configure_logging()
        return run(args.batch_size)
    except OSError as err:
        if err.errno == errno.EMFILE:
            logging.warning('BirdNET worker ran out of file descriptors.', exc_info=True)
            return EXIT_FD_LIMIT_REACHED
        logging.exception('BirdNET worker encountered an unexpected OS error.')
        return EXIT_UNEXPECTED_ERROR
    except SQLAlchemyError:
        logging.critical('BirdNET worker encountered a database error.', exc_info=True)
        return EXIT_DATABASE_ERROR
    except Exception:
        logging.exception('BirdNET worker encountered an unexpected error.')
        return EXIT_UNEXPECTED_ERROR


if __name__ == "__main__":
    sys.exit(main())
