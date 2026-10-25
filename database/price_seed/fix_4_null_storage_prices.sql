-- Phase 5 PC Builder - correct four missed simulated price estimates.
-- Explanation: the original MySQL CSV export included 2.5" in four
-- Storage model names. The original generated seed SQL moved the double
-- quote to the end of the name, making the exact-model WHERE clause
-- match zero rows. These updates use ID, category, manufacturer,
-- a recognisable model prefix, and price IS NULL instead.
--
-- IMPORTANT: Prices below are DEMO ESTIMATES, NOT VERIFIED RETAIL PRICES.
-- Back up your DB before applying. The default is ROLLBACK for safety.
USE `pc_building_system`;
START TRANSACTION;

UPDATE `component`
SET `price` = CASE `component_id`
    WHEN 2517 THEN 35.00    -- SanDisk SSD PLUS 120GB
    WHEN 2521 THEN 125.00   -- Kingston A400 960GB
    WHEN 2540 THEN 35.00    -- Kingston A400 240GB
    WHEN 2564 THEN 130.00   -- TC SUNBOW X3 1TB
    END,
    `specifications` = JSON_SET(
        COALESCE(`specifications`, JSON_OBJECT()),
        '$.price_metadata',
        JSON_OBJECT(
            'type', 'synthetic_estimate',
            'currency', 'AUD',
            'estimated_at', '2026-10-25',
            'method', 'ai_assisted_rule_based_demo_v1',
            'confidence', 'low'
        )
    )
WHERE `price` IS NULL
  AND `category` = 'Storage'
  AND (
       (`component_id` = 2517 AND `manufacturer` = 'SanDisk'   AND `model` LIKE '%SSD PLUS%120GB%')
    OR (`component_id` = 2521 AND `manufacturer` = 'Kingston' AND `model` LIKE '%A400 960GB%')
    OR (`component_id` = 2540 AND `manufacturer` = 'Kingston' AND `model` LIKE '%A400 240GB%')
    OR (`component_id` = 2564 AND `manufacturer` = 'TC SUNBOW' AND `model` LIKE '%TCSUNBOW X3-1TB%')
  );

-- The number of updated rows should be 4 on the first run.
SELECT ROW_COUNT() AS updated_rows;

-- Preview the values within the transaction:
SELECT `component_id`, `manufacturer`, `model`, `price`,
       JSON_UNQUOTE(JSON_EXTRACT(`specifications`, '$.price_metadata.type')) AS `price_type`
FROM `component`
WHERE `component_id` IN (2517, 2521, 2540, 2564)
ORDER BY `component_id`;

SELECT COUNT(*) AS remaining_missing_prices FROM `component` WHERE `price` IS NULL;

-- PREVIEW ONLY: change to COMMIT; and rerun the whole script to save.
COMMIT;
