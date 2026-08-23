import logging

import pandas as pd
from sqlalchemy import select, Float, cast, insert
from database.tables import Recording_final, Microphone, Detection, BirdSpecies, DetectionProcessedRecordings
from corvium_core.database.tables import Media, Device

class DetectionService:
    def __init__(self, engine):
        self.engine = engine

    def get_recordings(self):
        stmt = (
            select(Recording_final.c.id.label('file_id'),
                   Recording_final.c.timestamp,
                   Recording_final.c.rec_date,
                   Recording_final.c.file_path,
                   Microphone.c.id.label('mic_id'),
                   Microphone.c.longitude,
                   Microphone.c.latitude
                   )
            .join(Microphone, Microphone.c.id==Recording_final.c.microphone_id)
        )

        try:
            with self.engine.connect() as conn:
                result = conn.execute(stmt)

                # Convert to DataFrame safely
                df = pd.DataFrame(result.mappings().all())
                return df

        except Exception as err:
            logging.error(f'Error getting recordings: {err}')
            return pd.DataFrame()

    def get_unprocessed_recordings(self, batch_size):
        """Return at most ``batch_size`` recordings without a completed detection.

        A processing-state row is written only after the recording's detections
        have been persisted, so its absence means the recording remains eligible
        for a later BirdNET worker.
        """
        stmt = (
            select(
                Recording_final.c.id.label('file_id'),
                Recording_final.c.timestamp,
                Recording_final.c.rec_date,
                Media.c.relative_filepath,
                Device.c.device_id.label('mic_id'),
                Device.c.longitude,
                Device.c.latitude,
            )
            .join(Device, Device.c.device_id == Recording_final.c.microphone_id)
            .join(Media, Media.c.media_id == Recording_final.c.id)
            .outerjoin(
                DetectionProcessedRecordings,
                DetectionProcessedRecordings.c.recording_id == Recording_final.c.id,
            )
            .where(DetectionProcessedRecordings.c.recording_id.is_(None))
            .limit(batch_size)
        )

        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return pd.DataFrame(result.mappings().all())


    def get_microphone_location(self, microphone_id):
        stmt = (
            select(
                cast(Device.c.latitude, Float).label("latitude"),
                cast(Device.c.longitude, Float).label("longitude"),
            )
            .where(Device.c.device_id == microphone_id)
        )

        with self.engine.connect() as conn:
            return conn.execute(stmt).mappings().first()


    def insert_detections(self, df):
        """Insert detections from a DataFrame into the ``Detection`` table.

        Only DataFrame columns whose names exist in ``Detection`` are inserted.
        This makes the DataFrame's column order irrelevant and ignores any
        additional prediction columns.
        """
        if df.empty:
            return

        detection_columns = [
            column.name for column in Detection.columns if column.name in df.columns
        ]

        if not detection_columns:
            logging.error('Cannot insert detections: no Detection columns in DataFrame')
            return

        try:
            with self.engine.begin() as conn:
                conn.execute(
                    insert(Detection),
                    df.loc[:, detection_columns].to_dict(orient="records"),
                )
        except Exception as err:
            logging.error(f'Cannot insert detections:\n{err}')

    def persist_detections_and_mark_processed(self, df, recording_id, model_version):
        """Persist one recording's detections, then mark it complete.

        The insert and processing-state write share a transaction.  Therefore a
        worker that exits between recordings never leaves a recording marked as
        processed without its detections, nor leaves persisted detections that
        would be reinserted by a replacement worker.
        """
        detection_columns = [
            column.name for column in Detection.columns if column.name in df.columns
        ]

        if not df.empty and not detection_columns:
            raise ValueError('Cannot insert detections: no Detection columns in DataFrame')

        with self.engine.begin() as conn:
            if not df.empty:
                conn.execute(
                    insert(Detection),
                    df.loc[:, detection_columns].to_dict(orient="records"),
                )
            conn.execute(
                insert(DetectionProcessedRecordings).values(
                    recording_id=recording_id,
                    model_version=model_version,
                )
            )

    def get_species_id(self, scientific_name):
        """
        Get the birdnet_is associated with the given scientific name. If a scientific name is not found, it falls back
        to the aliases (field: scientific_name_aliases).
        :param scientific_name:
        :return:
        """
        stmt = select(BirdSpecies.c.birdnet_id).where(BirdSpecies.c.scientific_name == scientific_name)
        stmt_alt = select(BirdSpecies.c.birdnet_id).where(BirdSpecies.c.scientific_name_aliases.contains(scientific_name))

        with self.engine.connect() as conn:
            birdnet_id = conn.execute(stmt).scalar()
            if birdnet_id is None:  # if the scientific name is not found, search the aliases
                return conn.execute(stmt_alt).scalar()
            return birdnet_id
