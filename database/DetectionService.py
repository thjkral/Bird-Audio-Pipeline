import logging
import pandas as pd
from sqlalchemy import select, Float, cast, insert
from database.tables import Recording_cleaned, Microphone, Detection, BirdSpecies

class DetectionService:
    def __init__(self, engine):
        self.engine = engine

    def get_recordings(self):
        stmt = (
            select(Recording_cleaned.c.id.label('file_id'),
                   Recording_cleaned.c.timestamp,
                   Recording_cleaned.c.rec_date,
                   Recording_cleaned.c.file_path,
                   Microphone.c.id.label('mic_id'),
                   Microphone.c.longitude,
                   Microphone.c.latitude
                   )
            .join(Microphone, Microphone.c.id==Recording_cleaned.c.microphone_id)
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


    def get_microphone_location(self, microphone_id):
        stmt = (
            select(
                cast(Microphone.c.latitude, Float).label("latitude"),
                cast(Microphone.c.longitude, Float).label("longitude"),
            )
            .where(Microphone.c.id == microphone_id)
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

    def get_species_id(self, scientific_name):
        """
        Get the birdnet_is associated with the given scientific name. If a scientific name is not found, it falls back
        to the aliases (field: scientific_name_aliases).
        :param scientific_name:
        :return:
        """
        stmt = select(BirdSpecies.c.birdnet_id).where(BirdSpecies.c.scientific_name == scientific_name)
        stmt_alt = select(BirdSpecies.c.birdnet_id).where(BirdSpecies.c.scientific_name_aliases.contains(scientific_name))

        try:
            with self.engine.connect() as conn:
                birdnet_id = conn.execute(stmt).scalar()
                if birdnet_id is None:  # if the scientific name is not found, search the aliases
                    with self.engine.begin() as conn:
                        birdnet_id = conn.execute(stmt_alt).scalar()
                        return birdnet_id
                else:
                    return birdnet_id
        except Exception as err:
            logging.error(f'Error getting species ID for {scientific_name}:\n {err}')
