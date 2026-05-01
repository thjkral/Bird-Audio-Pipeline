from sqlalchemy import Table, Column, String, Integer, ForeignKey, Time

from database.tables.base import metadata

Regime = Table(
    'Regime',
    metadata,
    Column('regime_id', Integer, primary_key=True, nullable=False),
        Column('microphone_id', String(10), ForeignKey("Microphone.id"), nullable=False),
        Column('variable', String(25), nullable=False),
        Column('start_datetime', Time, nullable=False),
        Column('stop_datetime', Time),
        Column('expected_value', Integer, nullable=False))