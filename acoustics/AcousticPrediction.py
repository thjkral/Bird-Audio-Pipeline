"""Acoustic-model predictions and their conversion to detection rows."""

import hashlib
import json


class AcousticPrediction:
    def __init__(
        self,
        model,
        file_path,
        custom_species_list,
        workers,
        batch_size,
        overlap_s,
        model_version,
    ):
        self.model = model
        self.file_path = file_path
        self.custom_species_list = custom_species_list
        self.workers = workers
        self.batch_size = batch_size
        self.overlap_s = overlap_s
        self.model_version = model_version
        self.detection_df = None

    def predict(self):
        """Run the acoustic model and return its predictions as a DataFrame."""
        predictions = self.model.predict(
            self.file_path,
            custom_species_list=self.custom_species_list,
            n_workers=self.workers,
            batch_size=self.batch_size,
            overlap_duration_s=self.overlap_s,
        )
        self.detection_df = predictions.to_dataframe()
        return self.detection_df

    @staticmethod
    def _generate_hashed_id(row):
        """Create a deterministic identifier from all values in a detection row."""
        hashtext = json.dumps(
            [
                {
                    "attribute": str(attribute),
                    "type": f"{type(value).__module__}.{type(value).__qualname__}",
                    "value": repr(value),
                }
                for attribute, value in sorted(row.items(), key=lambda item: str(item[0]))
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.md5(hashtext.encode("utf-8")).hexdigest()

    def transform_dataframe(self, recording_id, geo_predictor):
        """Return predictions shaped for the Detection table.

        This method only transforms data. Persisting the returned DataFrame is
        deliberately the caller's responsibility.
        """
        dataframe = self._get_detection_dataframe().copy()
        geo_matches = dataframe["species_name"].apply(geo_predictor.get_confidence)
        dataframe["geo_confidence_score"] = geo_matches.map(lambda match: match[0])
        dataframe["birdnet_id"] = geo_matches.map(lambda match: match[1])
        dataframe = dataframe.rename(
            columns={
                "start_time": "window_start_s",
                "end_time": "window_stop_s",
                "confidence": "confidence_score",
            }
        )
        dataframe["recording_id"] = recording_id
        dataframe["model_version"] = self.model_version
        dataframe["overlap_s"] = self.overlap_s
        dataframe["detection_id"] = dataframe.apply(
            self._generate_hashed_id,
            axis=1,
        )
        self.detection_df = dataframe
        return self.detection_df

    def _get_detection_dataframe(self):
        if self.detection_df is None:
            raise RuntimeError("Call predict() before transforming predictions.")
        return self.detection_df
