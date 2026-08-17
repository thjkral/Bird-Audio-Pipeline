from sqlalchemy import Table, Column, String, Date, Time, Integer, DateTime, TIMESTAMP
from database.tables.base import metadata

Recording_final= Table(
    "audio_Recording_final",
    metadata,
    Column("id", String(64), primary_key=True, nullable=False),
    Column("file_name", String(255)),
    Column("microphone_id", String(10), nullable=False),
    Column("rec_date", Date, nullable=False),
    Column("start_time", Time, nullable=False),
    Column("stop_time", Time, nullable=False),
    Column('timestamp', DateTime, nullable=False),
    Column('timestamp_DST_adjusted', TIMESTAMP, nullable=False),
    Column("duration", Integer, nullable=False),
    Column("file_path", String(255), nullable=False),
    Column("file_size", Integer, nullable=False),
    Column("samplerate", Integer, nullable=False),
    Column("channels", Integer, nullable=False),
    Column("bitdepth", Integer, nullable=False),
    Column("file_hash", String(64), unique=True, nullable=False),
)