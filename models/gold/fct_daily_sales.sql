WITH silver_data AS (
    SELECT * FROM {{ ref('stg_events') }}
)
SELECT 
    DATE_TRUNC('day', event_time) AS event_date,
    category_code,
    COUNT(DISTINCT user_id) AS total_users,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS total_orders,
    ROUND(SUM(CASE WHEN event_type = 'purchase' THEN price ELSE 0 END), 2) AS total_revenue
FROM silver_data
GROUP BY 1, 2
