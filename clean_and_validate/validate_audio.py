'''
Go over the data to find anomalies
'''

import pandas as pd
import numpy as np
import ruptures as rpt
import logging

from database import ValidationService

def _run_cpd(dataframe, variable_to_validate):
    # get microphone IDs
    microphone_ids = dataframe['microphone_id'].unique().tolist()

    for mic_id in microphone_ids:
        mic_subset = dataframe[dataframe['microphone_id'] == mic_id].sort_values('timestamp')
        signal = mic_subset[variable_to_validate].values.reshape(-1, 1)

        model = rpt.Pelt(model='l2')
        change_points = model.fit(signal).predict(pen=10)

        for cp in change_points[:-1]: # each timestamp is the start of a new regime
            print(f"Detected change point moment= {mic_subset.iloc[cp]['timestamp']}")


def validate(db_engine):
    validation_service = ValidationService(db_engine)

    # Do CPD
    logging.info('Validation step 1: Change Point Detection')
    values_to_test = ['duration', 'file_size', 'samplerate', 'channels', 'bitdepth']
    for value in values_to_test:
        cpd_resume_point = validation_service.get_variable_resume_point(value)
        value_dataframe = validation_service.get_new_recordings(value, cpd_resume_point)
        logging.info(f'For variable {value}, {len(value_dataframe)} unprocessed recordings detected.')

        _run_cpd(value_dataframe, value)

