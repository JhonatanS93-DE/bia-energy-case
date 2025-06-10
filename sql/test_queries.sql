select * FROM enriched_postcodes;

select COUNT (*) FROM enriched_postcodes;

SELECT 
  COUNT(*) FILTER (WHERE postcode IS NULL) AS null_postcode,
  COUNT(*) FILTER (WHERE country IS NULL) AS null_country,
  COUNT(*) FILTER (WHERE latitude IS NULL) AS null_latitude,
  COUNT(*) FILTER (WHERE longitude IS NULL) AS null_longitude
FROM enriched_postcodes;

SELECT 
  ROUND(COUNT(*) FILTER (WHERE postcode IS NULL) * 100.0 / COUNT(*), 2) AS pct_null_postcode,
  ROUND(COUNT(*) FILTER (WHERE country IS NULL) * 100.0 / COUNT(*), 2) AS pct_null_country,
  ROUND(COUNT(*) FILTER (WHERE latitude IS NULL) * 100.0 / COUNT(*), 2) AS pct_null_latitude,
  ROUND(COUNT(*) FILTER (WHERE longitude IS NULL) * 100.0 / COUNT(*), 2) AS pct_null_longitude
FROM enriched_postcodes;

SELECT
    COUNT(*) FILTER (WHERE postcode IS NULL)*100.0 / COUNT(*) AS pct_null_postcode,
    COUNT(*) FILTER (WHERE country IS NULL)*100.0 / COUNT(*) AS pct_null_country,
    COUNT(DISTINCT postcode) AS distinct_postcodes,
    AVG(distance) AS avg_distance_to_postcode
FROM enriched_postcodes;