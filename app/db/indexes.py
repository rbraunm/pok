# indexes.py
from db import DB_PREFIX
from applogging import get_logger
import re

logger = get_logger(__name__)

INDEX_PREFIX = f"{DB_PREFIX}"
_len_re = re.compile(r"^`?([^`()]+)`?(?:\((\d+)\))?$")

# ---------- desired definitions ----------

def _indexDefs():
  d = [
    # loottable_entries
    ("loottable_entries", "lootdrop_id", ["lootdrop_id"]),
    ("loottable_entries", "loottable_id", ["loottable_id"]),
    ("loottable_entries", "lootdrop_loottable", ["lootdrop_id", "loottable_id"]),

    # merchantlist
    ("merchantlist", "item_minexp_maxexp", ["item", "min_expansion", "max_expansion"]),
    ("merchantlist", "merchantid", ["merchantid"]),
    ("merchantlist", "merchantid_minmaxexp", ["merchantid", "min_expansion", "max_expansion"]),

    # npc_types
    ("npc_types", "loottable_id", ["loottable_id"]),
    ("npc_types", "merchant_id", ["merchant_id"]),
    ("npc_types", "name", ["name"]),
    ("npc_types", "raid_target", ["raid_target"]),
    ("npc_types", "rare_spawn", ["rare_spawn"]),

    # spawnentry
    ("spawnentry", "npcID", ["npcID"]),
    ("spawnentry", "spawngroupID", ["spawngroupID"]),
    ("spawnentry", "npc_spawngroup", ["npcID", "spawngroupID"]),
    ("spawnentry", "npcid_chance", ["npcID", "chance"]),
    ("spawnentry", "minmaxexp", ["min_expansion", "max_expansion"]),
    ("spawnentry", "npc_minmax_chance", ["npcID","min_expansion","max_expansion","chance"]),

    # spawn2
    ("spawn2", "spawngroup_zone", ["spawngroupID", "zone"]),
    ("spawn2", "spawn2_minmaxexp", ["min_expansion", "max_expansion"]),
    ("spawn2", "zone_minmaxexp", ["zone", "min_expansion", "max_expansion"]),
    ("spawn2", "group_minmax_zone", ["spawngroupID", "min_expansion", "max_expansion", "zone"]),

    # tradeskill_recipe
    ("tradeskill_recipe", "expansion_range", ["min_expansion", "max_expansion"]),
    ("tradeskill_recipe", "tradeskill_skill_trivial_enabled",
      ["tradeskill", "skillneeded", "trivial", "enabled", "min_expansion", "max_expansion"]),

    # tradeskill_recipe_entries
    ("tradeskill_recipe_entries", "item_success_comp", ["item_id", "successcount", "componentcount"]),
    ("tradeskill_recipe_entries", "recipe_item", ["recipe_id", "item_id"]),

    # items
    ("items", "slots", ["slots"]),
    ("items", "classes", ["classes"]),
    ("items", "races", ["races"]),
    ("items", "reqlevel", ["reqlevel"]),
    ("items", "itemtype", ["itemtype"]),
    ("items", "scrolleffect", ["scrolleffect"]),
    ("items", "focuseffect", ["focuseffect"]),
    ("items", "slots_classes_races_levels", ["slots", "classes", "races", "reqlevel", "reclevel"]),

    # lootdrop_entries
    ("lootdrop_entries", "item_id_only", ["item_id"]),
    ("lootdrop_entries", "item_exp", ["item_id", "min_expansion", "max_expansion"]),
    ("lootdrop_entries", "itemid_lootdropid", ["item_id", "lootdrop_id"]),
    ("lootdrop_entries", "itemid_chance", ["item_id", "chance"]),
    ("lootdrop_entries", "lootdropid_minmaxexp", ["lootdrop_id", "min_expansion", "max_expansion"]),

    # character_spells
    ("character_spells", "spell_id_char_id", ["spell_id", "id"]),

    # character_data
    ("character_data", "id_deleted", ["id", "deleted_at"]),
    ("character_data", "name_deleted", ["name", "deleted_at"]),
    ("character_data", "deleted_name", ["deleted_at", "name"]),

    # rule_values
    ("rule_values", "rulename", ["rule_name"]),

    # spells_new
    ("spells_new", "name_only", ["name"]),
    ("spells_new", "id_name", ["id", "name"]),
    ("spells_new", "class_levels", [f"classes{n}" for n in range(1, 17)]),
    *[("spells_new", f"class_{n}", [f"classes{n}"]) for n in range(1, 17)],

    # {DB_PREFIX}_item_sources (dynamic table name)
    (f"{DB_PREFIX}_item_sources", "lootdrop_notnull", ["lootdropEntries(192)"]),
    (f"{DB_PREFIX}_item_sources", "merchant_notnull", ["merchantListEntries(192)"]),
    (f"{DB_PREFIX}_item_sources", "quest_notnull", ["questEntries(192)"]),
    (f"{DB_PREFIX}_item_sources", "recipe_notnull", ["tradeskillRecipeEntries(192)"]),
    (f"{DB_PREFIX}_item_sources", "item_sources_cols",
      ["lootdropEntries(192)", "merchantListEntries(192)", "tradeskillRecipeEntries(192)", "questEntries(192)"]),
  ]
  return d

def _parseColSpec(colSpec):
  m = _len_re.match(colSpec.strip())
  if not m:
    raise ValueError(f"Bad column spec: {colSpec}")
  col = m.group(1)
  sub = int(m.group(2)) if m.group(2) else None
  return col, sub

def _desiredMap():
  desired = {}
  for table, base, cols in _indexDefs():
    name = f"{INDEX_PREFIX}_{base}"
    colPairs = [_parseColSpec(c) for c in cols]
    desired.setdefault(table, {})[name] = {"cols": colPairs, "non_unique": 1}
  return desired

def _colListSQL(colPairs):
  return ", ".join(f"`{c}`({s})" if s is not None else f"`{c}`" for c, s in colPairs)

# ---------- metadata + normalization helpers ----------

def _getColMeta(cur):
  """
  Returns {(table, column): {"char_len": int|None, "octet_len": int|None, "data_type": str}}.
  No schema filter; assumes single-tenant DB as per environment notes.
  """
  cur.execute("""
    SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_MAXIMUM_LENGTH, CHARACTER_OCTET_LENGTH, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
  """)
  meta = {}
  for r in (cur.fetchall() or []):
    if isinstance(r, dict):
      tbl, col = r["TABLE_NAME"], r["COLUMN_NAME"]
      char_len = r["CHARACTER_MAXIMUM_LENGTH"]
      octet_len = r["CHARACTER_OCTET_LENGTH"]
      dtype = (r["DATA_TYPE"] or "").lower()
    else:
      tbl, col, char_len, octet_len, dtype = r
      dtype = (dtype or "").lower()
    try:
      char_len = int(char_len) if char_len is not None else None
    except Exception:
      char_len = None
    try:
      octet_len = int(octet_len) if octet_len is not None else None
    except Exception:
      octet_len = None
    meta[(tbl, col)] = {"char_len": char_len, "octet_len": octet_len, "data_type": dtype}
  return meta

def _isTextLike(dtype: str) -> bool:
  return dtype in {"text","tinytext","mediumtext","longtext","blob","tinyblob","mediumblob","longblob"}

def _normalizeExisting(existing, colMeta):
  """
  Mutates `existing` in-place: if SUB_PART means 'effectively full length', set it to None.
  Heuristics:
    - If SUB_PART is None, leave it.
    - If column has CHARACTER_MAXIMUM_LENGTH and SUB_PART >= that, treat as full (None).
    - For TEXT/BLOB families (no fixed char cap), treat SUB_PART >= 3072 bytes as full.
  """
  for table, idxs in existing.items():
    for idxName, info in idxs.items():
      new_cols = []
      for (col, sub) in info["cols"]:
        if sub is None:
          new_cols.append((col, None))
          continue
        meta = colMeta.get((table, col), {})
        char_len = meta.get("char_len")
        dtype = meta.get("data_type", "")
        if isinstance(char_len, int) and char_len > 0 and sub >= char_len:
          new_cols.append((col, None))
          continue
        if _isTextLike(dtype) and sub >= 3072:
          new_cols.append((col, None))
          continue
        new_cols.append((col, sub))
      info["cols"] = new_cols

# ---------- existing-index fetch & compare ----------

def _fetchExistingOurPrefix(cur):
  sql = """
    SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME, SUB_PART
    FROM information_schema.statistics
    WHERE INDEX_NAME LIKE %s
    ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
  """
  cur.execute(sql, (f"{INDEX_PREFIX}_%",))
  rows = cur.fetchall() or []

  existing = {}
  for r in rows:
    if isinstance(r, dict):
      table = r["TABLE_NAME"]; idx = r["INDEX_NAME"]; nonu = int(r["NON_UNIQUE"])
      seq = int(r["SEQ_IN_INDEX"]); col = r["COLUMN_NAME"]; sub = r["SUB_PART"]
    else:
      table, idx, nonu, seq, col, sub = r
      nonu = int(nonu); seq = int(seq)

    if sub is not None:
      try:
        sub = int(sub)
      except Exception:
        sub = None

    tmap = existing.setdefault(table, {})
    imap = tmap.setdefault(idx, {"cols": [], "non_unique": nonu})
    imap["cols"].append((col, sub))

  return existing

def _fetchAllIndexes(cur):
  """
  Returns {table: {index_name: {"cols":[(col,sub),...], "non_unique": int}}} for ALL indexes.
  """
  sql = """
    SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME, SUB_PART
    FROM information_schema.statistics
    ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
  """
  cur.execute(sql)
  rows = cur.fetchall() or []

  allidx = {}
  for r in rows:
    if isinstance(r, dict):
      table = r["TABLE_NAME"]; idx = r["INDEX_NAME"]; nonu = int(r["NON_UNIQUE"])
      seq = int(r["SEQ_IN_INDEX"]); col = r["COLUMN_NAME"]; sub = r["SUB_PART"]
    else:
      table, idx, nonu, seq, col, sub = r
      nonu = int(nonu); seq = int(seq)

    if sub is not None:
      try:
        sub = int(sub)
      except Exception:
        sub = None

    tmap = allidx.setdefault(table, {})
    imap = tmap.setdefault(idx, {"cols": [], "non_unique": nonu})
    imap["cols"].append((col, sub))

  return allidx

def _cmpCols(a, b):
  if len(a) != len(b):
    return False
  for (c1, s1), (c2, s2) in zip(a, b):
    if c1 != c2 or s1 != s2:
      return False
  return True

def _findFunctionalDuplicate(allIdxMap, table, desiredCols, desiredNonUnique, skipName):
  """
  Returns the name of a conflicting index on `table` whose (cols, non_unique) match `desired`,
  excluding `skipName`. If none, returns None.
  """
  haveByName = allIdxMap.get(table, {})
  for name, info in haveByName.items():
    if name == skipName:
      continue
    if int(info.get("non_unique", 1)) != int(desiredNonUnique):
      continue
    if _cmpCols(info.get("cols", []), desiredCols):
      return name
  return None

# ---------- helpers for DDL ----------

def _createIndex(cur, table, idxName, cols, non_unique):
  colSQL = _colListSQL(cols)
  stmtType = "CREATE INDEX" if int(non_unique) == 1 else "CREATE UNIQUE INDEX"
  cur.execute(f"{stmtType} `{idxName}` ON `{table}` ({colSQL})")
  logger.info(f"Created index `{idxName}` on `{table}` ({colSQL})")

def _dropIndex(cur, table, idxName, why):
  cur.execute(f"DROP INDEX `{idxName}` ON `{table}`")
  logger.info(f"Dropped index `{idxName}` on `{table}` ({why})")

# ---------- single-pass sync ----------

def syncIndexes(db):
  """
  Single-pass index sync:
    - Drop stray indexes with our prefix that aren't defined anymore.
    - Create missing desired indexes.
    - For mismatches, drop then recreate — BUT first check for functional duplicates
      (same cols/order & same uniqueness). If found, log a warning and SKIP our index.
  """
  desired = _desiredMap()
  changed = False

  with db.cursor() as cur:
    existingOur = _fetchExistingOurPrefix(cur)
    allExisting = _fetchAllIndexes(cur)
    colMeta = _getColMeta(cur)
    _normalizeExisting(existingOur, colMeta)
    _normalizeExisting(allExisting, colMeta)

    # 1) Drop stray indexes (present but not in definitions) — only our prefix
    for table, haveByName in sorted(existingOur.items()):
      wantByName = desired.get(table, {})
      for idxName in sorted(haveByName.keys()):
        if idxName not in wantByName:
          try:
            _dropIndex(cur, table, idxName, "not in definitions")
            changed = True
          except Exception as e:
            logger.exception("Exception in db/indexes.py")
            logger.exception(f"FAILED to drop `{idxName}` on `{table}`: {e}")

    # 2) Upsert desired indexes
    for table, wantByName in desired.items():
      haveByName = existingOur.get(table, {})
      for idxName, want in wantByName.items():
        have = haveByName.get(idxName)

        # If some other index already provides the same functionality, skip ours.
        dupe = _findFunctionalDuplicate(
          allExisting, table, want["cols"], want["non_unique"], skipName=idxName
        )
        if dupe:
          logger.warning(
            f"Skipping index `{idxName}` on `{table}`: functional duplicate exists `{dupe}` "
            f"(same columns/order and non_unique={want['non_unique']})"
          )
          # Do NOT drop or create our index in this case
          continue

        # Already correct? skip
        if have and _cmpCols(have["cols"], want["cols"]) and int(have["non_unique"]) == int(want["non_unique"]):
          logger.info(f"Index `{idxName}` on `{table}` is up-to-date; skipping")
          continue

        # If exists but mismatched: drop first
        if have:
          try:
            reasons = []
            if not _cmpCols(have["cols"], want["cols"]):
              reasons.append(f"cols differ (have={_colListSQL(have['cols'])} want={_colListSQL(want['cols'])})")
            if int(have["non_unique"]) != int(want["non_unique"]):
              reasons.append(f"non_unique differ (have={have['non_unique']} want={want['non_unique']})")
            _dropIndex(cur, table, idxName, "; ".join(reasons) or "definition differs")
            changed = True
          except Exception as e:
            logger.exception("Exception in db/indexes.py")
            logger.exception(f"FAILED to drop `{idxName}` on `{table}`: {e}")
            continue  # don't attempt create if drop failed

        # Create (missing or after drop)
        try:
          _createIndex(cur, table, idxName, want["cols"], want["non_unique"])
          changed = True
        except Exception as e:
          logger.exception("Exception in db/indexes.py")
          logger.exception(f"FAILED to create `{idxName}` on `{table}`: {e}")

  if changed:
    db.commit()

def initializeIndexes(db):
  logger.info("Checking indexes...")
  syncIndexes(db)
