from .adjust_for_dst import start as adjust_for_dst
from .check_bird_species import start as check_bird_species
import logging

def transform(db_engine):
    logging.info('STAGE: Transforming data')

    # Adjust recordings for Daylight Savings
    adjust_for_dst(db_engine)

    # Populate BirdSpecies table if empty
    check_bird_species(db_engine)

    logging.info('COMPLETED: Transforming data')
