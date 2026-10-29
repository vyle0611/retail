{{ config(materialized='table') }}

SELECT
    ROW_NUMBER() OVER (ORDER BY event_time, user_id, product_id) AS purchase_key,
    CAST(event_time AS DATE) AS date_key,
    event_time,
    user_id,
    product_id,
    price AS revenue
FROM {{ ref('stg_events') }}
WHERE event_type = 'purchase'
  AND user_id IS NOT NULL AND product_id IS NOT NULL
