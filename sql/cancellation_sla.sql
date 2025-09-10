-- Question 3(part a)
USE company_db;

WITH cancellations AS (
    SELECT
        order_id,
        created_at,
        canceled_at,
        TIMESTAMPDIFF(MINUTE, created_at, canceled_at) AS cancel_diff_minutes
    FROM
        orders
    WHERE
        canceled_at IS NOT NULL
)

SELECT
    (SELECT COUNT(*) FROM orders) AS total_orders,
    (SELECT COUNT(*) FROM cancellations) AS canceled,
    (SELECT COUNT(*) FROM cancellations WHERE cancel_diff_minutes > 60) AS violations,
    ROUND(
        100.0 * (SELECT COUNT(*) FROM cancellations WHERE cancel_diff_minutes > 60) * 1.0 / 
        (SELECT COUNT(*) FROM cancellations),
        2
    ) AS violation_rate_pct;
-- Question 3(part b)
USE company_db;

SELECT
    IF(TRIM(m.detected_intent) = '' OR m.detected_intent IS NULL, 'unknown', m.detected_intent) AS intent,
    COUNT(DISTINCT o.session_id) AS purchase_sessions
FROM messages m
JOIN orders o ON m.session_id = o.session_id
WHERE o.canceled_at IS NULL
GROUP BY intent
ORDER BY purchase_sessions DESC
LIMIT 2;
