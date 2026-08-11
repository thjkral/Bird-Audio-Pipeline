from sqlalchemy import Table, Column, String, TIMESTAMP, text, Float, ForeignKey
from database.tables.base import metadata

DetectionProcessedRecordings = Table(
    'audio_DetectionProcessedRecordings',
    metadata,
    Column('recording_id', String(64), ForeignKey('audio_Recording_cleaned.id'), primary_key=True),
    Column('processed_at', TIMESTAMP, server_default=text("CURRENT_TIMESTAMP()"), nullable=False),
    Column('model_version', Float, nullable=False),
)