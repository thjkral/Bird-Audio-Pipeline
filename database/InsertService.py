import Engine
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

class InsertService(Engine):
    def __init__(self, user, password, database):
        super().__init__(user, password, database)

    def insert_staging_recording(self, recording_object, batch_id):
        """
        Inserts a recording into Recording_staging. Transaction-safe.
        """
        query_text = text(f"""
            INSERT INTO Recording_staging(
                id,
                file_name,
                microphone_id,
                rec_date,
                start_time,
                stop_time,
                duration,
                file_path,
                file_size,
                samplerate,
                channels,
                bitdepth,
                file_hash,
                batch_id
            ) VALUES (
                :id, :filename, :microphone_id, :rec_date, :start_time, :stop_time,
                :duration, :file_path, :file_size, :samplerate, :channels,
                :bitdepth, :file_hash, :batch_id
            )
        """)
        params = recording_object.to_db_params(batch_id)

        try:
            with Session(self.engine) as session:
                session.execute(query_text, params)
                session.commit()
            return "Success"
        except Exception as err:
            logging.error(f'Cannot add recording {recording_object.filename}:\n{err}')
            return None
