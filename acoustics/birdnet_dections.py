import logging
import birdnet

from datetime import datetime
from .AcousticPrediction import AcousticPrediction
from database.DetectionService import DetectionService
from .GeoPrediction import GeoPrediction


def birdnet_week(dt):
    """
    Convert a datetime into BirdNET's 48-week numbering.
    """
    week_in_month = min((dt.day - 1) // 7 + 1, 4)
    return (dt.month - 1) * 4 + week_in_month

def start_acoustics_detection(db_engine):

    logging.info('Acoustics detection started')
    detection_service = DetectionService(db_engine)

    logging.info('Setting up the birdnet models')
    geo_model = birdnet.load("geo", "2.4", "tf", lang='nl')
    model = birdnet.load("acoustic", "2.4", "tf", lang='nl')

    logging.info('Retrieving recordings')
    recordings = detection_service.get_recordings()
    no_of_recordings = len(recordings)
    recording_index = 1
    logging.info(f'Retrieved {no_of_recordings} recordings')

    start_time = datetime.now()
    no_of_detections = 0

    recordings["week_number"] = recordings.apply(
        lambda row: birdnet_week(row["timestamp"]),
        axis=1,
    )

    week_numbers = recordings["week_number"].unique().tolist()
    for week_number in week_numbers:
        mic_ids = recordings.loc[
            recordings["week_number"] == week_number, "mic_id"
        ].unique().tolist()
        for mic_id in mic_ids:
            logging.info(f'Retrieving recordings for week_number {week_number} and mic_id {mic_id}')
            recordings_subset = recordings[(recordings["week_number"] == week_number)
                                           & (recordings["mic_id"] == mic_id)].copy()

            mic_location = detection_service.get_microphone_location(mic_id)

            geo_predictor = GeoPrediction(geo_model,
                                          mic_location.get('latitude'),
                                          mic_location.get('longitude'),
                                          week_number,
                                          0.01,
                                          detection_service)
            geo_predictor.predict()

            for _, recording in recordings_subset.iterrows():
                acoustic_predictor = AcousticPrediction(
                    model,
                    recording['file_path'],
                    custom_species_list=geo_predictor.get_prediction_as_set(),
                    workers=8,
                    batch_size=16,
                    overlap_s=1.5,
                    model_version=2.4,
                )
                acoustic_predictor.predict()

                if acoustic_predictor.detection_df.empty:
                    logging.info(f'No detections. Moving on to next recording')
                else:
                    predictions_df = acoustic_predictor.transform_dataframe(
                        recording['file_id'],
                        geo_predictor,
                    )
                    no_of_detections += len(predictions_df)

                    print(f'Analyzed {recording_index} of {no_of_recordings} recordings', flush=True)
                    recording_index += 1
                    detection_service.insert_detections(predictions_df)

    # Calulate the total run time in the prefered format
    stop_time = datetime.now()
    running_time = stop_time - start_time
    total_minutes = int(running_time.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)

    #Print and log a short summary
    logging.info(
        f'Detection run completed: \n'
        f'Runtime: {hours} hours {minutes} minutes. \n'
        f'Files: {no_of_recordings} recordings\n'
        f'Total detections: {no_of_detections} detections'
    )
