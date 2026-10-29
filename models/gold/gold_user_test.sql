{{ config(materialized='table') }}

SELECT DISTINCT user_id, product_id
FROM {{ ref('stg_events') }}
WHERE event_type = 'purchase'
  AND user_id IS NOT NULL AND product_id IS NOT NULL
  AND event_time >= TIMESTAMP '2019-11-24'
