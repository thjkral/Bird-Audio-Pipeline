from sqlalchemy import Table, Column, String, Integer, TIMESTAMP, text, ForeignKey
from database.tables.base import metadata

RegimeMappings = Table(
    'RegimeMappings',
    metadata,
    Column('mapping_id', String(64), primary_key=True),
    Column('rec_id', String(64),ForeignKey('Recording_cleaned.id') , nullable=False),
    Column('regime_id', Integer, ForeignKey('Regime.regime_id'), nullable=False),
    Column("created", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP()")))