import logging
import pandas as pd
from sqlalchemy import select
from database.tables import Recording_cleaned, Microphone

class DetectionService:
    def __init__(self, engine):
        self.engine = engine

    def get_recordings(self):
        stmt = (
            select(Recording_cleaned.c.file_hash,
                   Recording_cleaned.c.timestamp,
                   Recording_cleaned.c.rec_date,
                   Recording_cleaned.c.file_path,
                   Microphone.c.id,
                   Microphone.c.longitude,
                   Microphone.c.latitude
                   )
            .join(Microphone, Microphone.c.id==Recording_cleaned.c.microphone_id)
        )

        try:
            with self.engine.connect() as conn:
                result = conn.execute(stmt)

                # Convert to DataFrame safely
                df = pd.DataFrame(result.mappings().all())
                return df

        except Exception as err:
            logging.error(f'Error getting recordings: {err}')
            return pd.DataFrame()