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

    print("Ensuring indexes exist for query performance...")
    INDEX_DEFINITIONS = [
      # loottable_entries
      ("loottable_entries", "pok_idx_lootdrop_id", ["lootdrop_id"]),
      ("loottable_entries", "pok_idx_loottable_id", ["loottable_id"]),
      ("loottable_entries", "pok_idx_lootdrop_loottable", ["lootdrop_id", "loottable_id"]),

      # merchantlist
      ("merchantlist", "pok_idx_item_minexp_maxexp", ["item", "min_expansion", "max_expansion"]),
      ("merchantlist", "pok_idx_merchantid", ["merchantid"]),
      ("merchantlist", "pok_idx_merchantid_minmaxexp", ["merchantid", "min_expansion", "max_expansion"]),

      # npc_types
      ("npc_types", "pok_idx_loottable_id", ["loottable_id"]),
      ("npc_types", "pok_idx_merchant_id", ["merchant_id"]),

      # spawnentry
      ("spawnentry", "pok_idx_npcID", ["npcID"]),
      ("spawnentry", "pok_idx_spawngroupID", ["spawngroupID"]),
      ("spawnentry", "pok_idx_npc_spawngroup", ["npcID", "spawngroupID"]),
      ("spawnentry", "pok_idx_npcid_chance", ["npcID", "chance"]),
      ("spawnentry", "pok_idx_minmaxexp", ["min_expansion", "max_expansion"]),

      # spawn2
      ("spawn2", "pok_idx_spawngroup_zone", ["spawngroupID", "zone"]),
      ("spawn2", "pok_idx_spawn2_minmaxexp", ["min_expansion", "max_expansion"]),
      ("spawn2", "pok_idx_zone_minmaxexp", ["zone", "min_expansion", "max_expansion"]),

      # tradeskill_recipe
      ("tradeskill_recipe", "pok_idx_expansion_range", ["min_expansion", "max_expansion"]),
      ("tradeskill_recipe", "pok_idx_tradeskill_skill_trivial_enabled", ["tradeskill", "skillneeded", "trivial", "enabled", "min_expansion", "max_expansion"]),

      # tradeskill_recipe_entries
      ("tradeskill_recipe_entries", "pok_idx_item_success_comp", ["item_id", "successcount", "componentcount"]),
      ("tradeskill_recipe_entries", "pok_idx_recipe_item", ["recipe_id", "item_id"]),

      # items
      ("items", "pok_idx_slots_classes_races_levels", ["slots", "classes", "races", "reqlevel", "reclevel"]),
      ("items", "pok_idx_reqlevel", ["reqlevel"]),
      ("items", "pok_idx_slots", ["slots"]),
      ("items", "pok_idx_classes", ["classes"]),
      ("items", "pok_idx_races", ["races"]),
      ("items", "pok_idx_itemtype", ["itemtype"]),
      ("items", "pok_idx_scrolleffect", ["scrolleffect"]),

      # lootdrop_entries
      ("lootdrop_entries", "pok_idx_item_id_only", ["item_id"]),
      ("lootdrop_entries", "pok_idx_item_exp", ["item_id", "min_expansion", "max_expansion"]),
      ("lootdrop_entries", "pok_idx_itemid_lootdropid", ["item_id", "lootdrop_id"]),
      ("lootdrop_entries", "pok_idx_itemid_chance", ["item_id", "chance"]),
      ("lootdrop_entries", "pok_idx_lootdropid_minmaxexp", ["lootdrop_id", "min_expansion", "max_expansion"]),

      # character_spells
      ("character_spells", "pok_idx_spell_id_char_id", ["spell_id", "id"]),

      # character_data
      ("character_data", "pok_idx_id_deleted", ["id", "deleted_at"]),
      ("character_data", "pok_idx_name_deleted", ["name", "deleted_at"]),
      ("character_data", "pok_idx_deleted_name", ["deleted_at", "name"]),

      # rule_values
      ("rule_values", "pok_idx_rulename", ["rule_name"]),

      # spells_new
      ("spells_new", "pok_idx_name_only", ["name"]),
      ("spells_new", "pok_idx_id_name", ["id", "name"]),
      ("spells_new", "pok_idx_class_levels", [f"classes{n}" for n in range(1, 17)]),

      # zone
      ("zone", "pok_idx_short_name_expansion", ["short_name", "expansion"]),
      ("zone", "pok_idx_short_minmaxexp", ["short_name", "min_expansion", "max_expansion"])
    ]

    def getExistingIndexes(cur, table):
      cur.execute(f"SHOW INDEX FROM {table}")
      indexInfo = {}
      for row in cur.fetchall():
        idxName = row['Key_name']
        colName = row['Column_name']
        seqInIndex = row['Seq_in_index']
        if idxName not in indexInfo:
          indexInfo[idxName] = []
        indexInfo[idxName].append((seqInIndex, colName))
      return {k: [col for _, col in sorted(v)] for k, v in indexInfo.items()}

    for table, indexName, columns in INDEX_DEFINITIONS:
      existingIndexes = getExistingIndexes(cur, table)
      matchingIndex = None
      for existingName, existingCols in existingIndexes.items():
        if existingCols == columns:
          matchingIndex = existingName
          break

      if indexName in existingIndexes:
        if existingIndexes[indexName] != columns:
          print(f"Dropping mismatched index '{indexName}' on '{table}' (was on {existingIndexes[indexName]}, expected {columns})")
          cur.execute(f"DROP INDEX {indexName} ON {table}")
          cur.execute(f"CREATE INDEX {indexName} ON {table} ({', '.join(columns)})")
          print(f"Recreated index '{indexName}' on '{table}' with columns {columns}")
        else:
          print(f"Index '{indexName}' on '{table}' is correct, skipping")
      elif matchingIndex:
        print(f"Table '{table}' already has index '{matchingIndex}' on columns {columns}, skipping creation of '{indexName}'")
      else:
        cur.execute(f"CREATE INDEX {indexName} ON {table} ({', '.join(columns)})")
        print(f"Created index '{indexName}' on '{table}' with columns {columns}")

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
      WHERE (se.chance > 0)
        AND (se.min_expansion <= currentExpansion)
        AND (se.max_expansion = -1 OR se.max_expansion >= currentExpansion)
        AND (s2.min_expansion <= currentExpansion)
        AND (s2.max_expansion = -1 OR s2.max_expansion >= currentExpansion)
        AND (z.min_expansion <= currentExpansion)
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
      WHERE (ml.min_expansion <= currentExpansion)
        AND (ml.max_expansion = -1 OR ml.max_expansion >= currentExpansion)
        AND (se.chance > 0)
        AND (se.min_expansion <= currentExpansion)
        AND (se.max_expansion = -1 OR se.max_expansion >= currentExpansion)
        AND (s2.min_expansion <= currentExpansion)
        AND (s2.max_expansion = -1 OR s2.max_expansion >= currentExpansion)
        AND (z.min_expansion <= currentExpansion)
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
        AND tr.enabled = 1
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