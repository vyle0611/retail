{{ config(materialized='table') }}

SELECT
    user_id,
    product_id,
    COUNT(CASE WHEN event_type = 'view' THEN 1 END)     AS view_count,
    COUNT(CASE WHEN event_type = 'cart' THEN 1 END)     AS cart_count,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchase_count,
    SUM(CASE event_type WHEN 'purchase' THEN 3 WHEN 'cart' THEN 2 ELSE 1 END) AS total_score
FROM {{ ref('stg_events') }}
WHERE user_id IS NOT NULL AND product_id IS NOT NULL
  AND event_time < TIMESTAMP '2019-11-24'
GROUP BY user_id, product_id
