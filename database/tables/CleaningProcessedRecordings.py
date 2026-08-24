from sqlalchemy import Table, Column, String, TIMESTAMP, text, Boolean
from database.tables.base import pipeline_metadata

CleaningProcessedRecordings = Table(
    'audio_CleaningProcessedRecordings',
    pipeline_metadata,
    Column('recording_id', String(64), primary_key=True, nullable=False),
    Column('passed', Boolean, nullable=False),
    Column('processed_at', TIMESTAMP, server_default=text("CURRENT_TIMESTAMP()"), nullable=False)
)