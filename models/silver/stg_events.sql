WITH raw_data AS (
    SELECT * FROM {{ source('motherduck', 'bronze_raw_events') }}
)
SELECT 
    CAST(event_time AS TIMESTAMP) AS event_time,
    event_type,
    product_id,
    category_id,
    COALESCE(category_code, 'unknown') AS category_code,
    COALESCE(brand, 'unknown') AS brand,
    price,
    user_id
FROM raw_data
WHERE price >= 0
