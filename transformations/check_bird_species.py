"""Populate the BirdSpecies table from the bundled BirdNET taxonomy if needed."""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import insert, select

from database.tables import BirdSpecies


TAXONOMY_FILE = (
    Path(__file__).resolve().parents[1]
    / "utils"
    / "files"
    / "birdnet_taxonomy_0.3-Jul2026.csv"
)

# These are the fields selected by utils/add_bird_species_list.py.  The
# duplicate ``scientific_name_aliases`` entry in that script is intentionally
# omitted: selecting it twice creates a DataFrame with duplicate column names.
TAXONOMY_COLUMNS = [
    "birdnet_id",
    "scientific_name",
    "scientific_name_aliases",
    "common_name",
    "common_name_alt",
    "taxon_group",
    "record_type",
    "common_name_aliases",
    "inat_id",
    "ebird_code",
    "gbif_id",
    "ncbi_id",
    "avibase_id",
    "birdlife_id",
    "ml_taxon_code",
    "xc_name",
    "observationorg_id",
    "wikidata_qid",
    "observations_count",
    "description_source",
    "metadata_quality_score",
    "metadata_quality_flags",
    "image_url",
    "image_author",
    "image_license",
    "image_source",
    "common_name_en",
    "common_name_nl",
]


def start(db_engine):
    """Add the bundled BirdNET bird species only when the table is empty."""
    logging.info('Checking if BirdSpecies table is empty.')
    try:
        if check_if_empty(db_engine):
            logging.info("BirdSpecies is empty; loading the BirdNET taxonomy.")
            insert_bird_species(db_engine)
        else:
            logging.info("BirdSpecies already contains data; skipping taxonomy load.")
    except Exception:
        # This is a final safeguard so initialising the taxonomy cannot crash
        # the caller's pipeline.
        logging.exception("Could not initialise the BirdSpecies table.")


def check_if_empty(db_engine):
    """Return ``True`` when ``BirdSpecies`` has no rows.

    A database error returns ``False`` deliberately: the caller must not risk
    inserting duplicate taxonomy rows when it cannot verify the table state.
    """
    try:
        statement = select(BirdSpecies.c.birdnet_id).limit(1)
        with db_engine.connect() as connection:
            return connection.execute(statement).first() is None
    except Exception:
        logging.exception("Could not check whether BirdSpecies is empty.")
        return False


def load_and_transform_dataframe():
    """Load the BirdNET taxonomy and return its non-null Aves subset."""
    try:
        dataframe = pd.read_csv(TAXONOMY_FILE, usecols=TAXONOMY_COLUMNS)
        aves_dataframe = dataframe.loc[dataframe["taxon_group"] == "Aves"].fillna("")

        logging.info("Loaded %s bird species from %s.", len(aves_dataframe), TAXONOMY_FILE)
        return aves_dataframe
    except (OSError, ValueError, pd.errors.ParserError):
        logging.exception("Could not load BirdNET taxonomy from %s.", TAXONOMY_FILE)
        return pd.DataFrame()
    except Exception:
        logging.exception("Could not transform the BirdNET taxonomy.")
        return pd.DataFrame()


def insert_bird_species(db_engine):
    """Insert the transformed BirdNET taxonomy into ``BirdSpecies``."""
    try:
        dataframe = load_and_transform_dataframe()
        if dataframe.empty:
            logging.warning("BirdNET taxonomy contains no bird species to insert.")
            return

        table_columns = [
            column.name for column in BirdSpecies.columns if column.name in dataframe.columns
        ]
        if not table_columns:
            logging.error("BirdNET taxonomy has no columns that match BirdSpecies.")
            return

        records = dataframe.loc[:, table_columns].to_dict(orient="records")
        with db_engine.begin() as connection:
            connection.execute(insert(BirdSpecies), records)

        logging.info("Inserted %s bird species into BirdSpecies.", len(records))
    except Exception:
        logging.exception("Could not insert bird species into BirdSpecies.")
