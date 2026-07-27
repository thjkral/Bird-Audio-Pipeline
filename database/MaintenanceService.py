from database.tables.base import metadata
from sqlalchemy import inspect, insert
from database.tables import BirdSpecies
import logging


class DatabaseMaintenance():
    def __init__(self, engine):
        self.engine = engine

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

    def insert_bird_species(self, dataframe):
        """Insert BirdSpecies rows from matching DataFrame columns.

        Columns in ``dataframe`` that are not part of the BirdSpecies table are
        ignored, so their order and any additional source metadata do not
        affect the insert.
        """
        if dataframe.empty:
            return

        bird_species_columns = [
            column.name for column in BirdSpecies.columns
            if column.name in dataframe.columns
        ]

        if not bird_species_columns:
            logging.error(
                "Cannot insert BirdSpecies: no BirdSpecies columns in DataFrame"
            )
            return

        try:
            with self.engine.begin() as conn:
                conn.execute(
                    insert(BirdSpecies),
                    dataframe.loc[:, bird_species_columns].to_dict(orient="records"),
                )
        except Exception as err:
            logging.error(f"Cannot insert BirdSpecies:\n{err}")
