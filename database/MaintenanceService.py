from database.Engine import Engine
from database.tables.base import metadata
import database.tables
from sqlalchemy import inspect
import logging


class DatabaseMaintenance(Engine):
    def __init__(self, db_credentials):
        super().__init__(db_credentials)

    def create_tables_if_not_exist(self):
        logging.info(f"Checking if required tables exist in the database")
        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names())

        for table in metadata.tables.values():
            if table.name not in existing_tables:
                print(f"Creating table: {table.name}")
                table.create(self.engine)
            else:
                print(f"Table exists: {table.name}")