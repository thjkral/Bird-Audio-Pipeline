CREATE OR REPLACE VIEW audio_agg_DetectionOverTime AS (
    SELECT
        bs.common_name_nl AS Soort,
        rec.rec_date AS Datum,
        COUNT(*) AS "Aantal detecties",
        COUNT(DISTINCT d.recording_id) AS "Aantal opnames"
    FROM audio_Detection AS d
    JOIN audio_BirdSpecies as bs
        ON d.birdnet_id=bs.birdnet_id
    JOIN audio_Recording_final AS rec
        ON d.recording_id=rec.id
    GROUP BY bs.common_name_nl, rec.rec_date
    ORDER BY rec.rec_date
);