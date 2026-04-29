import pandas as pd
import logging
from sqlalchemy import select
from database.tables import Recording_cleaned
from database.tables import CPD_processing_state

class ValidationService:
    def __init__(self, engine):
        self.engine = engine


    def get_variable_resume_point(self, variable):
        stmt = (select(CPD_processing_state.c.last_processed_timestamp).where(CPD_processing_state.c.variable == variable))

        try:
            with self.engine.connect() as conn:
                result = conn.execute(stmt)
                resume_point = result.scalar_one_or_none()
                logging.info(f'Most recently processed {variable} for CPD: {resume_point}')
                return resume_point
        except Exception as e:
            logging.error(f'Cannot fetch most recent timestamp for variable {variable}:\n{e}')
            return None


    def get_new_recordings(self, variable: str, last_ts):

        var_column = getattr(Recording_cleaned.c, variable)

        stmt = (
            select(Recording_cleaned.c.id,
                   Recording_cleaned.c.timestamp,
                   var_column,
                   Recording_cleaned.c.microphone_id)
            .where(Recording_cleaned.c.timestamp > last_ts)
        )

        try:
            with self.engine.connect() as conn:
                result = conn.execute(stmt)

                # Convert to DataFrame safely
                df = pd.DataFrame(result.mappings().all())
                return df

        except Exception as err:
            logging.error(f'Cannot fetch recordings for variable {variable}:\n{err}')
            return pd.DataFrame()
