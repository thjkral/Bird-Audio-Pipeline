from sqlalchemy import Table, Column, String, Date, Time, Integer, TIMESTAMP, text
from database.tables.base import metadata

Recording_staging = Table(
    "Recording_staging",
    metadata,
    Column("id", String(64)),
    Column("file_name", String(255)),
    Column("microphone_id", String(10)),
    Column("rec_date", Date),
    Column("start_time", Time),
    Column("stop_time", Time),
    Column('timestamp', TIMESTAMP),
    Column("duration", Integer),
    Column("file_path", String(255)),
    Column("file_size", Integer),
    Column("samplerate", Integer),
    Column("channels", Integer),
    Column("bitdepth", Integer),
    Column("file_hash", String(64)),
    Column("batch_id", Integer, nullable=False),
    Column("ingestion_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP()")),
)