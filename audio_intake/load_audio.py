"""
Go over the filesystem, detect new audio, extract data and store in database
"""

import os
import logging
import shutil
from .Recording import Recording
from database import InsertService


def _get_wav_files(root_dir, batch_size, skipped_paths=None):
    """Return a batch of .wav file paths under ``root_dir``.

    Paths in ``skipped_paths`` are ignored for the duration of a load run.
    This lets failed files remain at their source without being retried forever
    by the batch loop.
    """
    logging.info(f'Getting a new batch of recordings')
    if skipped_paths is None:
        skipped_paths = set()

    recordings_list = []
    for current_dir, _, files in os.walk(root_dir):
        for file in files:
            filename = os.fsdecode(file)
            if filename.endswith('.wav'):
                full_path = os.path.join(current_dir, filename)
                if full_path in skipped_paths:
                    continue

                recordings_list.append(full_path)
                if len(recordings_list) == batch_size:
                    logging.info(
                        f'{len(recordings_list)} files in batch. '
                        'Preparing to move them to new location and database.'
                    )
                    return recordings_list

    # The scan is exhausted before a full batch was collected.  Return this
    # final partial batch so that the remaining recordings are processed.
    logging.info(f'{len(recordings_list)} files in batch. Preparing to move them to new location and database.')
    return recordings_list


def _move_recording_file(recording):
    """Move a recording from its intake path to its storage path."""
    try:
        os.makedirs(os.path.dirname(recording.new_file_path_abs), exist_ok=True)
        shutil.move(recording.old_file_path, recording.new_file_path_abs)
    except Exception as err:
        logging.error(f'Problem while moving file {recording.old_file_path} to {recording.new_file_path_abs}:\n{err}')


def _remove_empty_directories(root_dir):
    """Remove empty directories below ``root_dir``, keeping the root intact."""
    logging.info('Removing empty directories')
    for current_dir, _, _ in os.walk(root_dir, topdown=False):
        if current_dir == root_dir:
            continue

        try:
            os.rmdir(current_dir)
            logging.info('Removed empty directory: %s', current_dir)
        except OSError:
            # A directory containing files (or one changed by another process)
            # is intentionally left in place.
            continue


def start_load(config, db_engine):
    '''
    Loops over all audio files in a given directory, creates objects and saves them to the database.
    :param: Root folder where all data is stored
    '''

    inserter = InsertService(db_engine)

    logging.info(f'Looking for data at location: {config.root_dir}.')

    skipped_paths = set()
    while True:
        wav_files = _get_wav_files(config.root_dir, config.batch_size, skipped_paths=skipped_paths)
        if wav_files is None or len(wav_files) == 0:
            logging.info(f'There are no processable .wav files left in {config.root_dir}. Audio intake completed!')
            break
        else:
            for file_path in wav_files:
                filename = os.path.basename(file_path)
                try:
                    rec = Recording(file_path, filename)
                except Exception as err:
                    skipped_paths.add(file_path)
                    logging.warning(
                        'Skipping recording %s because it could not be initialized: %s',
                        file_path,
                        err,
                    )
                    continue

                try:
                    rec.set_new_filepath(config.store_dir)
                except Exception as err:
                    skipped_paths.add(rec.old_file_path)
                    logging.warning(
                        'Skipping recording %s because it could not be prepared for loading: %s',
                        rec.old_file_path,
                        err,
                    )
                    continue

                try:
                    result = inserter.insert_staging_recording(rec)
                except Exception as err:
                    skipped_paths.add(rec.old_file_path)
                    logging.warning(
                        'Skipping recording %s because its data could not be written to the database: %s',
                        rec.old_file_path,
                        err,
                    )
                    continue

                if result != 'Success':
                    skipped_paths.add(rec.old_file_path)
                    logging.warning(
                        'Skipping recording %s because its data could not be written to the database.',
                        rec.old_file_path,
                    )
                    continue

                _move_recording_file(rec)
                logging.info(f'Processed recording: {rec.filename}')

            logging.info(f'Loaded {len(wav_files)} .wav files.')

    _remove_empty_directories(config.root_dir)
