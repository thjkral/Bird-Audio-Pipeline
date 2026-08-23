from sqlalchemy import Table, Column, String, Numeric
from database.tables.base import pipeline_metadata

Microphone = Table(
    "audio_Microphone",
    pipeline_metadata,
    Column("id", String(10), primary_key=True, nullable=False),
    Column("longitude", Numeric(9, 6)),
    Column("latitude", Numeric(8, 6)),
    Column("description", String(500)),
)