CREATE OR REPLACE VIEW audio_agg_DetectionHeatmap AS (
    SELECT
        bs.common_name_nl AS Soort,
        rec.rec_date AS Datum,
        HOUR(rec.start_time) AS Uur,
        COUNT(*) AS Aantal
    FROM audio_Detection AS d
    JOIN audio_BirdSpecies as bs
        ON d.birdnet_id=bs.birdnet_id
    JOIN audio_Recording_final AS rec
        ON d.recording_id=rec.id
    GROUP BY bs.common_name_nl, rec.rec_date, rec.start_time
);