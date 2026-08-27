CREATE OR REPLACE VIEW audio_agg_Rare_Observations AS (
    SELECT
        species.common_name_nl AS Soort,
        rec.rec_date AS Datum,
        s.name_nl AS Seizoen,
        d.birdnet_week_number AS Birdnet_week,
        flag.name_nl AS Gradatie,
        COUNT(*) AS Aantal
    FROM audio_Detection as d
    LEFT JOIN audio_BirdSpecies AS species
        ON d.birdnet_id=species.birdnet_id
    LEFT JOIN audio_Recording_final AS rec
        ON d.recording_id=rec.id
    LEFT JOIN core_GeoConfidenceFlag AS flag
        ON d.geo_confidence_score >= flag.min_value AND d.geo_confidence_score <= flag.max_value
    JOIN core_Season AS s
        ON (
            s.wraps_year = 0
            AND MONTH(rec.timestamp_DST_adjusted) BETWEEN s.start_month AND s.stop_month
        )
        OR (
            s.wraps_year = 1
            AND (
                MONTH(rec.timestamp_DST_adjusted) >= s.start_month
                OR MONTH(rec.timestamp_DST_adjusted) <= s.stop_month
            )
        )
    WHERE d.confidence_score >= 0.5 AND d.geo_confidence_score < 0.2
    GROUP BY species.common_name_nl, rec.rec_date, flag.name_nl, s.name_nl, d.birdnet_week_number
);