DROP TABLE IF EXISTS audio_agg_DetectionHeatmap;
CREATE TABLE IF NOT EXISTS audio_agg_DetectionHeatmap AS (
    SELECT
        bs.common_name_nl AS Soort,
        rec.rec_date AS Datum,
        rec.start_time AS Tijd,
        COUNT(*) AS Aantal
    FROM audio_Detection AS d
    JOIN core_BirdSpecies as bs
        ON d.birdnet_id=bs.birdnet_id
    JOIN audio_Recording_cleaned AS rec
        ON d.recording_id=rec.id
    GROUP BY bs.common_name_nl, rec.rec_date, rec.start_time
);