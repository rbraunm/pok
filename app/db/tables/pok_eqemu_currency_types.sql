-- Do another pass and base this table off the alternate_currencies table more directly, IE: use the alternate currency ID for the id here as a foreign/primary key
-- Maybe pull the LDoN themes into its own table so it can be derived in here too.
CREATE TABLE pok_eqemu_currency_types (
  id               SMALLINT UNSIGNED PRIMARY KEY,
  name             VARCHAR(64)  NOT NULL,
  short_name       VARCHAR(32)  NOT NULL UNIQUE,
  icon_id          INT UNSIGNED NULL,

  -- Theme/variant hints where applicable
  ldon_theme_id    TINYINT UNSIGNED NULL,
  don_variant_id   TINYINT UNSIGNED NULL,

  -- Item backed currencies
  item_id          INT UNSIGNED NULL
) COMMENT='Merchant currency types';

-- Coin
SELECT 1 AS id, 
  'Copper' AS name, 
  'copper' AS short_name, 
  582  AS icon_id,  
  NULL as ldon_theme_id,  
  NULL AS don_variant_id,  
  NULL AS item_id
UNION ALL 

-- LDoN Points
SELECT 2, 'LDoN Points - Any Theme',            'ldon_any',     1437,  0,     NULL,  NULL
UNION ALL                  
SELECT 3, 'LDoN Points - Deepest Guk',          'ldon_guk',     1437,  1,     NULL,  NULL
UNION ALL                    
SELECT 4, 'LDoN Points - Miragul''s Menagerie', 'ldon_mir',     1437,  2,     NULL,  NULL
UNION ALL                  
SELECT 5, 'LDoN Points - Mistmoore Catacombs',  'ldon_mmc',     1437,  3,     NULL,  NULL
UNION ALL                    
SELECT 6, 'LDoN Points - Rujarkian Hills',      'ldon_ruj',     1437,  4,     NULL,  NULL
UNION ALL                    
SELECT 7, 'LDoN Points - Takish-Hiz',           'ldon_tak',     1437,  5,     NULL,  NULL
UNION ALL     

-- DoN Crystals       
SELECT 20, 'Radiant Crystals',                  'don_radiant',  NULL,  NULL,  1,     rc.item_id
FROM (
  SELECT MIN(i.id) AS item_id
  FROM items i
  WHERE TRIM(i.Name) = 'Radiant Crystal'
) rc
WHERE rc.item_id IS NOT NULL

UNION ALL

SELECT 21, 'Ebon Crystals',                     'don_ebon',     NULL,  NULL,  2,     ec.item_id
FROM (
  SELECT MIN(i.id) AS item_id
  FROM items i
  WHERE TRIM(i.Name) = 'Ebon Crystal'
) ec
WHERE ec.item_id IS NOT NULL

UNION ALL

-- Item Backed Currencies
SELECT
  100 + ac.id AS id,
  TRIM(i.Name) AS name,
  LEFT(CONCAT('alt_', LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(i.Name),' ','_'),'''',''),'-','_'),'/','_'),'(',''),')',''))), 32) AS short_name,
  NULL AS icon_id,
  NULL AS ldon_theme_id,
  NULL AS don_variant_id,
  ac.item_id AS item_id
FROM alternate_currency ac
JOIN items i ON i.id = ac.item_id
WHERE TRIM(i.Name) NOT IN ('Radiant Crystal','Ebon Crystal');
