import logging
from sqlalchemy import text, insert
from database.tables import Recording_staging

class InsertService():
    def __init__(self, engine):
        self.engine = engine


    def _recording_to_staging_dict(self, recording, batch_id):
        """
        Maps a Recording domain object to a dict matching Recording_staging table.
        """
        return {
            "id": recording.rec_id,
            "file_name": recording.filename,
            "microphone_id": recording.mic_id,
            "rec_date": recording.rec_date,
            "start_time": recording.start_time,
            "stop_time": recording.stop_time,
            "timestamp": recording.timestamp,
            "duration": recording.duration,
            "file_path": recording.new_file_path,
            "file_size": recording.filesize,
            "samplerate": recording.samplerate,
            "channels": recording.channels,
            "bitdepth": recording.bitdepth,
            "file_hash": recording.file_hash,
            "batch_id": batch_id
        }


    def insert_staging_recording(self, recording, batch_id):
        """
        Inserts a single recording into Recording_staging.
        """
        stmt = insert(Recording_staging)

        params = self._recording_to_staging_dict(recording, batch_id)

        try:
            with self.engine.begin() as conn:
                conn.execute(stmt, [params])
            return "Success"

        except Exception as err:
            logging.error(
                f'Cannot add recording {recording.filename}:\n{err}'
            )
            return None
