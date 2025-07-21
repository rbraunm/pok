import json
import pymysql.cursors

def getConfig():
  with open("/app/server/eqemu_config.json") as f:
    return json.load(f)

def getDb():
  cfg = getConfig()["server"]["database"]
  return pymysql.connect(
    host=cfg["host"],
    port=int(cfg["port"]),
    user=cfg["username"],
    password=cfg["password"],
    database=cfg["db"],
    cursorclass=pymysql.cursors.DictCursor,
    charset="utf8mb4"
  )

def initializeDbObjects():
  db = getDb()
  with db.cursor() as cur:
    print("Tuning session variables for query performance...")

    cur.execute("SET SESSION max_heap_table_size=1073741824")
    cur.execute("SET SESSION tmp_table_size=1073741824")
    cur.execute("SET SESSION sort_buffer_size=67108864")
    cur.execute("SET SESSION join_buffer_size=33554432")
    cur.execute("SET SESSION read_buffer_size=33554432")
    cur.execute("SET SESSION read_rnd_buffer_size=33554432")
    cur.execute("SET SESSION group_concat_max_len=131072")

    print("Creating pok_item_sources table if it does not exist...")

    cur.execute("""
      CREATE TABLE IF NOT EXISTS pok_item_sources (
        item_id INT PRIMARY KEY,
        lootdropEntries TEXT,
        merchantListEntries TEXT,
        tradeskillRecipeEntries TEXT,
        questEntries TEXT
      )
    """)

    print("Creating or replacing pok_populate_item_sources stored procedure...")

    cur.execute("DROP PROCEDURE IF EXISTS pok_populate_item_sources")

    cur.execute("""
    CREATE PROCEDURE pok_populate_item_sources()
    BEGIN
      DECLARE currentExpansion INT;

      -- Get current expansion
      SELECT rule_value INTO currentExpansion
      FROM rule_values
      WHERE rule_name = 'Expansion:CurrentExpansion';

      -- Clear the existing table
      TRUNCATE TABLE pok_item_sources;

      -- Insert lootdropEntries
      INSERT INTO pok_item_sources (item_id, lootdropEntries)
      SELECT
        i.id AS item_id,
        GROUP_CONCAT(DISTINCT lde.lootdrop_id ORDER BY lde.lootdrop_id) AS lootdropEntries
      FROM items i
      JOIN lootdrop_entries lde ON lde.item_id = i.id
      JOIN loottable_entries le ON lde.lootdrop_id = le.lootdrop_id
      JOIN loottable lt ON le.loottable_id = lt.id
      JOIN npc_types nt ON lt.id = nt.loottable_id
      JOIN spawnentry se ON nt.id = se.npcID
      JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
      JOIN zone z ON s2.zone = z.short_name
      WHERE
        (se.min_expansion = -1 OR se.min_expansion <= currentExpansion)
        AND (se.max_expansion = -1 OR se.max_expansion >= currentExpansion)
        AND (z.min_expansion = -1 OR z.min_expansion <= currentExpansion)
        AND (z.max_expansion = -1 OR z.max_expansion >= currentExpansion)
        AND z.expansion <= currentExpansion
      GROUP BY i.id
      ON DUPLICATE KEY UPDATE lootdropEntries = VALUES(lootdropEntries);

      -- Insert merchantListEntries
      INSERT INTO pok_item_sources (item_id, merchantListEntries)
      SELECT
        ml.item AS item_id,
        GROUP_CONCAT(DISTINCT ml.merchantid ORDER BY ml.merchantid) AS merchantListEntries
      FROM merchantlist ml
      JOIN npc_types nt ON nt.merchant_id = ml.merchantid
      JOIN spawnentry se ON nt.id = se.npcID
      JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
      JOIN zone z ON s2.zone = z.short_name
      WHERE
        (ml.min_expansion = -1 OR ml.min_expansion <= currentExpansion)
        AND (ml.max_expansion = -1 OR ml.max_expansion >= currentExpansion)
        AND (se.min_expansion = -1 OR se.min_expansion <= currentExpansion)
        AND (se.max_expansion = -1 OR se.max_expansion >= currentExpansion)
        AND (z.min_expansion = -1 OR z.min_expansion <= currentExpansion)
        AND (z.max_expansion = -1 OR z.max_expansion >= currentExpansion)
        AND z.expansion <= currentExpansion
      GROUP BY ml.item
      ON DUPLICATE KEY UPDATE merchantListEntries = VALUES(merchantListEntries);

      -- Insert tradeskillRecipeEntries
      INSERT INTO pok_item_sources (item_id, tradeskillRecipeEntries)
      SELECT
        tre.item_id,
        GROUP_CONCAT(DISTINCT tre.recipe_id ORDER BY tre.recipe_id) AS tradeskillRecipeEntries
      FROM tradeskill_recipe_entries tre
      JOIN tradeskill_recipe tr ON tre.recipe_id = tr.id
      WHERE tre.successcount > 0
        AND (tr.min_expansion = -1 OR tr.min_expansion <= currentExpansion)
        AND (tr.max_expansion = -1 OR tr.max_expansion >= currentExpansion)
      GROUP BY tre.item_id
      ON DUPLICATE KEY UPDATE tradeskillRecipeEntries = VALUES(tradeskillRecipeEntries);

      -- Placeholder for questEntries
      -- You can implement this similarly when quest logic is defined

    END
    """)

    print("Populating pok_item_sources table...")
    cur.execute("CALL pok_populate_item_sources()")
    db.commit()
    print("DB initialization completed.")

  db.close()
#      LEFT JOIN spawnentry se ON nt.id = se.npcID
#      LEFT JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
#      LEFT JOIN zone z ON s2.zone = z.short_name
#      WHERE nt.id = %s
#        AND (
#          (se.min_expansion = -1 OR se.min_expansion <= %s)
#          AND (se.max_expansion = -1 OR se.max_expansion >= %s)
#        )
#        AND (
#          (z.min_expansion = -1 OR z.min_expansion <= %s)
#          AND (z.max_expansion = -1 OR z.max_expansion >= %s)
#        )
#        AND (
#          z.expansion <= %s
#        )