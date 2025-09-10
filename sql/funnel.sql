-- Question 1
USE company_db;

WITH sessions AS (
    SELECT
        device,
        session_id,
        MAX(CASE WHEN event_name = 'Loaded' THEN 1 ELSE 0 END) AS Loaded,
        MAX(CASE WHEN event_name = 'Interact' THEN 1 ELSE 0 END) AS Interact,
        MAX(CASE WHEN event_name = 'Clicks' THEN 1 ELSE 0 END) AS Clicks,
        MAX(CASE WHEN event_name = 'Purchase' THEN 1 ELSE 0 END) AS Purchase
    FROM events
    GROUP BY device, session_id
),
step_counts AS (
    SELECT device, 'Loaded' AS step, COUNT(*) AS users FROM sessions WHERE Loaded = 1 GROUP BY device
    UNION ALL
    SELECT device, 'Interact', COUNT(*) AS users FROM sessions WHERE Interact = 1 GROUP BY device
    UNION ALL
    SELECT device, 'Clicks', COUNT(*) AS users FROM sessions WHERE Clicks = 1 GROUP BY device
    UNION ALL
    SELECT device, 'Purchase', COUNT(*) AS users FROM sessions WHERE Purchase = 1 GROUP BY device
),
conv AS (
    SELECT
        device,
        step,
        users,
        LAG(users) OVER (PARTITION BY device ORDER BY 
            CASE step 
                WHEN 'Loaded' THEN 1
                WHEN 'Interact' THEN 2
                WHEN 'Clicks' THEN 3
                WHEN 'Purchase' THEN 4
            END
        ) AS prev_users
    FROM step_counts
),
start_users AS (
    SELECT device, users AS loaded_users FROM step_counts WHERE step = 'Loaded'
)

SELECT
    c.step,
    c.users,
    ROUND(100.0 * c.users / c.prev_users, 2) AS conv_from_prev_pct,
    ROUND(100.0 * c.users / s.loaded_users, 2) AS conv_from_start_pct,
    c.device
FROM conv c
JOIN start_users s ON c.device = s.device
ORDER BY c.device,
    CASE c.step
        WHEN 'Loaded' THEN 1
        WHEN 'Interact' THEN 2
        WHEN 'Clicks' THEN 3
        WHEN 'Purchase' THEN 4
    END;
    
    
-- On desktop, the biggest drop happens from Interact (40 users) → Clicks (20 users) → Purchase (6 users).
-- This could be due to a cluttered interface or confusing navigation, making it hard for users to find products and proceed to purchase.

-- On mobile, although the initial steps perform better, there’s still a significant drop from Interact (47 users) → Clicks (25 users) → Purchase (9 users).
-- This could be because of small buttons, slow page load, or poor product display on smaller screens.

-- Across both devices, the consistent reduction in users at each step suggests friction in the flow — possibly long load times, unclear call-to-actions, or insufficient product information that prevents confident purchase decisions.
