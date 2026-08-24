from sqlalchemy import Table, Column, String, TIMESTAMP, text, Float, ForeignKey
from database.tables.base import pipeline_metadata

DetectionProcessedRecordings = Table(
    'audio_DetectionProcessedRecordings',
    pipeline_metadata,
    Column('recording_id', String(64), ForeignKey('audio_Recording_final.id'), primary_key=True),
    Column('processed_at', TIMESTAMP, server_default=text("CURRENT_TIMESTAMP()"), nullable=False),
    Column('model_version', Float, nullable=False),
)