import logging
import pandas as pd


def _check_null_values(dataframe, db, field_list=None):
    df_clean = dataframe.dropnna(axis=0,
                                 how='any',
                                 subset=field_list,
                                 inplace=True)
    df_nans = dataframe - df_clean
    #TODO: write nans to DB

    return df_clean


def _check_duplicates_batch(dataframe):
    pass


def _check_duplicates_historical(dataframe):
    pass


def start_clean(db_conn, batch_id):
    logging.info(f'Cleaning data with batch ID: {batch_id}')

    df_to_clean = db_conn.get_recordings_for_cleaning(batch_id)

    # Identify rows with missing values
    df_to_clean = _check_null_values(df_to_clean, db_conn)

    # Identify duplicate rows within the batch
