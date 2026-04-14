from sqlalchemy import Table, Column, Integer, String
from database.tables.base import metadata

Species = Table(
    "Species",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("scientific_name", String(300), unique=True, nullable=False),
    Column("common_name_eng", String(300), nullable=False),
    Column("common_name_nl", String(300)),
)