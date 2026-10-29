WITH silver_events AS (
    SELECT * FROM {{ ref('stg_events') }}
)
SELECT 
    user_id,
    product_id,
    COUNT(CASE WHEN event_type = 'view' THEN 1 END) AS view_count,
    COUNT(CASE WHEN event_type = 'cart' THEN 1 END) AS cart_count,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchase_count,
    -- Tính tổng điểm tương tác (Interaction Score): View=1, Cart=2, Purchase=3
    SUM(CASE 
        WHEN event_type = 'purchase' THEN 3 
        WHEN event_type = 'cart' THEN 2 
        ELSE 1 
    END) AS total_score
FROM silver_events
WHERE user_id IS NOT NULL AND product_id IS NOT NULL
GROUP BY user_id, product_id
