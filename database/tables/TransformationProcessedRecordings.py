from sqlalchemy import Table, Column, String, TIMESTAMP, text, ForeignKey
from database.tables.base import metadata

TransformationProcessedRecordings = Table(
    'audio_TransformationProcessedRecordings',
    metadata,
    Column('recording_id', String(64), ForeignKey('audio_Recording_cleaned.id'), primary_key=True),
    Column('processed_at', TIMESTAMP, server_default=text("CURRENT_TIMESTAMP()"), nullable=False)
)