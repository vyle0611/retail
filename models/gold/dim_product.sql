{{ config(materialized='table') }}

SELECT
    product_id,
    COALESCE(MAX(NULLIF(category_code, 'unknown')), 'unknown') AS category_code,
    COALESCE(MAX(brand), 'unknown')                            AS brand,
    ROUND(AVG(price), 2)                                       AS avg_price,
    MIN(price)                                                 AS min_price,
    MAX(price)                                                 AS max_price
FROM {{ ref('stg_events') }}
WHERE product_id IS NOT NULL
GROUP BY product_id
