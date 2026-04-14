from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey
from database.tables.base import metadata

Observation = Table(
    "Observation",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("rec_id", String(64), ForeignKey("Recording.id"), nullable=False),
    Column("species_id", Integer, ForeignKey("Species.id"), nullable=False),
    Column("start_second", Integer, nullable=False),
    Column("stop_second", Integer, nullable=False),
    Column("confidence_score", Float, nullable=False),
)