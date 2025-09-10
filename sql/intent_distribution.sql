-- Question 2 
USE company_db;

SELECT
    IF(TRIM(detected_intent) = '' OR detected_intent IS NULL, 'unknown', detected_intent) AS intent,
    COUNT(*) AS count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM messages), 2) AS pct_of_total
FROM
    messages
GROUP BY
    intent
ORDER BY
    count DESC;
    
-- the top 2 intents most correlated with Purchase are likely:
-- product_search
-- product_comparison
