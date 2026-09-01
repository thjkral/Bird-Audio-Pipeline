"""Classify staged audio recordings and persist the cleaning result.

The cleaning stage reads recordings that do not yet have a processing state,
evaluates every validation rule against every recording, and divides the batch
into accepted and rejected rows.

Validation rules are deliberately represented as independent boolean masks.
This means one rejected recording can retain several failure categories, such
as being both too short and a duplicate. Accepted recordings are written to
``Recording_cleaned`` and ``Media``; rejected recordings and their failure
flags are written to ``Recording_rejected``.
"""

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
    """Raise an informative error when required staging columns are absent.

    This checks the DataFrame structure, not the values in individual rows.
    Missing values within existing columns are handled later by the null mask
    and result in a normal rejected recording.

    :param dataframe: Staged recordings to validate.
    :raises ValueError: If one or more required columns are absent.
    """
    missing_columns = sorted(set(REQUIRED_FIELDS) - set(dataframe.columns))
    if missing_columns:
        raise ValueError(
            "Staged recordings are missing required columns: "
            + ", ".join(missing_columns)
        )


def _batch_duplicate_mask(dataframe):
    """Return a mask selecting duplicate IDs or file hashes in this batch.

    The first occurrence is considered the original and remains eligible for
    the other validation outcomes. Only later occurrences are marked as batch
    duplicates. Null identifiers are left to the null-value check and are not
    treated as duplicates merely because several rows contain nulls.

    :param dataframe: Complete batch of staged recordings.
    :return: Boolean Series aligned with ``dataframe.index``.
    """
    # A cleaned recording must have both a unique primary ID and a unique file
    # hash, so either repeated value is sufficient to identify a duplicate.
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

    Duration bounds are inclusive. Batch duplicates preserve their first
    occurrence as the original. Historical duplicates are detected using both
    IDs and file hashes when both are supplied by ``historic_recordings``.

    :param dataframe: Staged recordings that have no cleaning processing state.
    :param historic_recordings: Existing cleaned recording IDs and file hashes.
    :param min_duration: Shortest accepted duration, in seconds.
    :param max_duration: Longest accepted duration, in seconds.
    :return: Two DataFrames containing accepted and rejected recordings.
    :raises ValueError: If required columns are absent or the duration bounds
        are reversed.
    """
    # Treat no input and an empty batch as valid no-work cases. Copies keep the
    # function's non-mutating contract consistent for every return path.
    if dataframe is None:
        dataframe = pd.DataFrame()
    if dataframe.empty:
        return dataframe.copy(), dataframe.copy()
    if min_duration > max_duration:
        raise ValueError("Minimum duration cannot exceed maximum duration")

    _validate_columns(dataframe)
    # ingestion_at is staging audit metadata and belongs in neither destination
    # table. Work on a copy so callers can safely retain the original batch.
    classified = dataframe.drop(columns=["ingestion_at"], errors="ignore").copy()

    # These masks are intentionally calculated before filtering any rows. A
    # recording can therefore fail several tests and keep all relevant flags.
    null_mask = classified[REQUIRED_FIELDS].isna().any(axis=1)

    # Coercion makes malformed, non-numeric durations fail the range test
    # instead of raising an exception. A genuine null is recorded by is_null;
    # it is not also described as being outside the numeric range.
    numeric_duration = pd.to_numeric(classified["duration"], errors="coerce")
    duration_mask = classified["duration"].notna() & ~numeric_duration.between(
        min_duration, max_duration, inclusive="both"
    )

    batch_duplicate_mask = _batch_duplicate_mask(classified)

    # Historic comparison is set-based so each staged row is checked against
    # all recordings already admitted to Recording_cleaned.
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

    # A single is_duplicate flag controls rejection. duplicate_type preserves
    # whether the duplicate came from this batch or from cleaned history.
    duplicate_mask = batch_duplicate_mask | historical_duplicate_mask
    classified["is_null"] = null_mask
    classified["outside_range"] = duration_mask
    classified["is_duplicate"] = duplicate_mask
    classified["duplicate_type"] = None
    classified.loc[batch_duplicate_mask, "duplicate_type"] = "batch"
    # The current schema stores one duplicate subtype. If both apply,
    # historical is the more important provenance to retain.
    classified.loc[historical_duplicate_mask, "duplicate_type"] = "historical"

    # Eligibility is decided only after every flag has been attached. This is
    # the sole accepted/rejected split: zero failures means accepted; one or
    # more failures means rejected.
    failed_mask = classified[
        ["is_null", "outside_range", "is_duplicate"]
    ].any(axis=1)
    accepted = classified.loc[~failed_mask].copy()
    rejected = classified.loc[failed_mask].copy()
    return accepted, rejected


def start_clean(db_engine):
    """Classify and persist all staged recordings awaiting cleaning.

    ``CleaningService`` selects only staging rows without a corresponding
    ``CleaningProcessedRecordings`` entry. Rejected rows are saved first with
    their failure flags. Accepted rows are then saved to ``Recording_cleaned``
    and their relative paths to ``Media``. The service is responsible for the
    appropriate processing-state inserts for each group.

    :param db_engine: SQLAlchemy engine connected to the pipeline database.
    """
    logging.info("Cleaning process initiated")
    clean_service = CleaningService(db_engine)

    # The query excludes recordings already handled by an earlier cleaning run.
    batch_df = clean_service.get_recordings_for_cleaning()

    if batch_df is None or batch_df.empty:
        logging.info("No recordings found for cleaning")
        return

    # Historic identifiers are loaded once and reused for the complete batch.
    historic_recordings = clean_service.get_unique_historic_hashes()
    accepted, rejected = classify_recordings(batch_df, historic_recordings)

    logging.info(
        "Cleaning classified %d recordings: %d accepted and %d rejected",
        len(batch_df),
        len(accepted),
        len(rejected),
    )
    # Both service methods safely return without writing when their DataFrame is
    # empty, so a batch containing only accepted or only rejected rows is valid.
    clean_service.insert_rejected_recordings(rejected)
    clean_service.insert_cleaned_recordings(accepted)
    logging.info("Cleaning results saved successfully")
