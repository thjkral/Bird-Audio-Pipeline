from sqlalchemy import Table, Column, String, Numeric
from database.tables.base import metadata

Microphone = Table(
    "audio_Microphone",
    metadata,
    Column("id", String(10), primary_key=True, nullable=False),
    Column("longitude", Numeric(9, 6)),
    Column("latitude", Numeric(8, 6)),
    Column("description", String(500)),
)