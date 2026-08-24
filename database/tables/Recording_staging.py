from sqlalchemy import Table, Column, String, Date, Time, Integer, TIMESTAMP, text, DateTime, ForeignKey
from database.tables.base import pipeline_metadata

Recording_staging = Table(
    "audio_Recording_staging",
    pipeline_metadata,
    Column("id", String(64)),
    Column("file_name", String(255)),
    Column("microphone_id", String(10), ForeignKey("core_Device.device_id")),
    Column("rec_date", Date),
    Column("start_time", Time),
    Column("stop_time", Time),
    Column('timestamp', DateTime),
    Column("duration", Integer),
    Column("relative_file_path", String(255)),
    Column("file_size", Integer),
    Column("samplerate", Integer),
    Column("channels", Integer),
    Column("bitdepth", Integer),
    Column("file_hash", String(64)),
    Column("ingestion_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP()")),
)