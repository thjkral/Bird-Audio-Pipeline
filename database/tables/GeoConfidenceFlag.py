from sqlalchemy import Table, Column, Integer, String, Double
from database.tables.base import pipeline_metadata

GeoConfidenceFlag = Table(
    "audio_GeoConfidenceFlag",
    pipeline_metadata,
    Column("id", Integer, primary_key=True, nullable=False, autoincrement=True),
    Column("name_en", String(300), unique=True, nullable=False),
    Column("name_nl", String(300), unique=True, nullable=False),
    Column("max_value", Double, nullable=False),
    Column("min_value", Double, nullable=False),
    Column("description", String(600), nullable=True),
)