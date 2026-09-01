"""Classify staged audio recordings and persist the cleaning result."""

import logging

import pandas as pd

from database import CleaningService


MIN_DURATION_SECONDS = 60
MAX_DURATION_SECONDS = 600

# Every value needed by Recording_cleaned or Media must be present. Keep this
# list explicit so an unrelated staging/audit column cannot invalidate rows.
REQUIRED_FIELDS = [
    "id",
    "file_name",
    "microphone_id",
    "rec_date",
    "start_time",
    "stop_time",
    "timestamp",
    "duration",
    "relative_file_path",
    "file_size",
    "samplerate",
    "channels",
    "bitdepth",
    "file_hash",
]


def _validate_columns(dataframe):
    missing_columns = sorted(set(REQUIRED_FIELDS) - set(dataframe.columns))
    if missing_columns:
        raise ValueError(
            "Staged recordings are missing required columns: "
            + ", ".join(missing_columns)
        )


def _batch_duplicate_mask(dataframe):
    """Find rows that would violate either cleaned-table unique key."""
    duplicate_id = dataframe["id"].notna() & dataframe["id"].duplicated(
        keep="first"
    )
    duplicate_hash = dataframe["file_hash"].notna() & dataframe[
        "file_hash"
    ].duplicated(keep="first")
    return duplicate_id | duplicate_hash


def classify_recordings(
    dataframe,
    historic_recordings=None,
    min_duration=MIN_DURATION_SECONDS,
    max_duration=MAX_DURATION_SECONDS,
):
    """Return ``(accepted, rejected)`` without modifying ``dataframe``.

    Every check is evaluated independently against the full batch. Rejected
    rows therefore retain all applicable failure flags, while only rows with
    no failures are accepted.
    """
    if dataframe is None:
        dataframe = pd.DataFrame()
    if dataframe.empty:
        return dataframe.copy(), dataframe.copy()
    if min_duration > max_duration:
        raise ValueError("Minimum duration cannot exceed maximum duration")

    _validate_columns(dataframe)
    classified = dataframe.drop(columns=["ingestion_at"], errors="ignore").copy()

    null_mask = classified[REQUIRED_FIELDS].isna().any(axis=1)
    numeric_duration = pd.to_numeric(classified["duration"], errors="coerce")
    duration_mask = classified["duration"].notna() & ~numeric_duration.between(
        min_duration, max_duration, inclusive="both"
    )
    batch_duplicate_mask = _batch_duplicate_mask(classified)

    if historic_recordings is not None and not historic_recordings.empty:
        historic_ids = set(
            historic_recordings.get("id", pd.Series(dtype=object)).dropna()
        )
        historic_hashes = set(
            historic_recordings.get("file_hash", pd.Series(dtype=object)).dropna()
        )
        historical_duplicate_mask = classified["id"].isin(historic_ids) | classified[
            "file_hash"
        ].isin(historic_hashes)
    else:
        historical_duplicate_mask = pd.Series(False, index=classified.index)

    duplicate_mask = batch_duplicate_mask | historical_duplicate_mask
    classified["is_null"] = null_mask
    classified["outside_range"] = duration_mask
    classified["is_duplicate"] = duplicate_mask
    classified["duplicate_type"] = None
    classified.loc[batch_duplicate_mask, "duplicate_type"] = "batch"
    # The current schema stores one duplicate subtype. If both apply,
    # historical is the more important provenance to retain.
    classified.loc[historical_duplicate_mask, "duplicate_type"] = "historical"

    failed_mask = classified[
        ["is_null", "outside_range", "is_duplicate"]
    ].any(axis=1)
    accepted = classified.loc[~failed_mask].copy()
    rejected = classified.loc[failed_mask].copy()
    return accepted, rejected


def start_clean(db_engine):
    """Clean all staged recordings that do not have a processed state."""
    logging.info("Cleaning process initiated")
    clean_service = CleaningService(db_engine)
    batch_df = clean_service.get_recordings_for_cleaning()

    if batch_df is None or batch_df.empty:
        logging.info("No recordings found for cleaning")
        return

    historic_recordings = clean_service.get_unique_historic_hashes()
    accepted, rejected = classify_recordings(batch_df, historic_recordings)

    logging.info(
        "Cleaning classified %d recordings: %d accepted and %d rejected",
        len(batch_df),
        len(accepted),
        len(rejected),
    )
    clean_service.insert_rejected_recordings(rejected)
    clean_service.insert_cleaned_recordings(accepted)
    logging.info("Cleaning results saved successfully")
