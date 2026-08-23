from sqlalchemy import Table, Column, Integer, String, TIMESTAMP, ForeignKey, Double, Enum, text, Float
from database.tables.base import pipeline_metadata

Detection = Table(
    'audio_Detection',
    pipeline_metadata,
    Column('detection_id', String(64), primary_key=True, nullable=False),
    Column('recording_id', String(64), ForeignKey('core_Media.media_id'), nullable=False),
    Column('birdnet_id', String(10), ForeignKey('audio_BirdSpecies.birdnet_id'), nullable=False),
    Column("window_start_s", Double, nullable=False),
    Column("window_stop_s", Double, nullable=False),
    Column("confidence_score", Double, nullable=False),
    Column('overlap_s', Float, nullable=False),
    Column('geo_confidence_score', Double, nullable=False),
    Column('birdnet_week_number', Integer, nullable=False),
    Column('model_version', Float, nullable=False),
    Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP()")),
)
