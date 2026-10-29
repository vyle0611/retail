{{ config(materialized='table') }}

SELECT
    user_id,
    MIN(event_time)                                        AS first_seen,
    MAX(event_time)                                        AS last_seen,
    COUNT(CASE WHEN event_type = 'view'     THEN 1 END)   AS total_views,
    COUNT(CASE WHEN event_type = 'cart'     THEN 1 END)   AS total_carts,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)   AS total_purchases,
    ROUND(COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN price END), 0), 2) AS total_spent,
    CASE
        WHEN COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) = 0 THEN 'browser'
        WHEN COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) < 3 THEN 'buyer'
        ELSE 'loyal'
    END AS segment
FROM {{ ref('stg_events') }}
WHERE user_id IS NOT NULL
GROUP BY user_id
