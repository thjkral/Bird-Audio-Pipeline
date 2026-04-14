'''
Go over the data to find anomalies
'''

import pandas as pd
import logging


def _check_if_value_within_range(df, field, upper_val, lower_val):

    result_df = df.loc[(df[field] < lower_val) & (df[field] > upper_val)]
    no_of_abnormalities = len(result_df)

    if no_of_abnormalities > 0:
        logging.info(f'Field: {field} | Status: {no_of_abnormalities} deviants found')
        #TODO: write rows to database
    else:
        logging.info(f'Field: {field} | Status: OK')

#TODO: function to get expected values

def validate(db_conn):
    recordings_df = db_conn.get_recordings_for_validation()

    #TODO: for-loop with fields to validate
    _check_if_value_within_range(recordings_df, 'samplerate', 33000, 31000)
    #_samplerate_abnormalities_check(recordings_df)
