from sqlalchemy import Table, Column, String, Date, Time, Integer, DateTime, ForeignKey
from database.tables.base import pipeline_metadata
from corvium_core.database.tables.base import core_metadata


Recording_cleaned = Table(
    "audio_Recording_cleaned",
    pipeline_metadata,
    Column("id", String(64), ForeignKey('core_Media.media_id'), primary_key=True, nullable=False),
    Column("file_name", String(255)),
    Column("microphone_id", String(10), ForeignKey("core_Device.device_id"), nullable=False),
    Column("rec_date", Date, nullable=False),
    Column("start_time", Time, nullable=False),
    Column("stop_time", Time, nullable=False),
    Column('timestamp', DateTime, nullable=False),
    Column("duration", Integer, nullable=False),
    Column("file_size", Integer, nullable=False),
    Column("samplerate", Integer, nullable=False),
    Column("channels", Integer, nullable=False),
    Column("bitdepth", Integer, nullable=False),
    Column("file_hash", String(64), unique=True, nullable=False),
)