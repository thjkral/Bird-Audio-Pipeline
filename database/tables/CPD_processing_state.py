from sqlalchemy import Table, Column, String, TIMESTAMP

from database.tables.base import metadata

CPD_processing_state = Table(
    'CPD_processing_state',
    metadata,
    Column('variable', String(64), nullable=False, primary_key=True),
    Column('last_processed_timestamp', TIMESTAMP, nullable=False))

