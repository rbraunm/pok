from applogging import get_logger
from db import DB_PREFIX
import os
import glob
import re

logger = get_logger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
TABLES_SQL_DIR = os.path.join(HERE, "tables")

# ===== Regex (case-insensitive) =====
# Capture the table name in a CREATE TABLE header
_HDR_RE = re.compile(r"CREATE\s+TABLE\s+`?([A-Za-z0-9_]+)`?", flags=re.IGNORECASE)
# Rewrite the identifier in the CREATE header while preserving "CREATE TABLE "
_CREATE_RE = re.compile(r"(CREATE\s+TABLE\s+)`?[A-Za-z0-9_]+`?", flags=re.IGNORECASE)
# Match exactly "INSERT INTO <name>" and capture the leading prefix for safe replacement
_INS_INTO_TARGET_RE_TMPL = r"(?i)(\bINSERT\s+INTO\s+)`?{name}`?"
# Strip any number of leading comments and whitespace:
#  - line comments: -- ... (to end of line)
#  - block comments: /* ... */
_LEADING_COMMENTS_RE = re.compile(
  r"^\s*(?:(?:--[^\n]*\n)|(?:/\*.*?\*/\s*))*",
  flags=re.DOTALL | re.MULTILINE
)

def _prefixed(name: str) -> str:
  pref = f"pok_"
  return name if name.startswith(pref) else f"{pref}{name}"

def _rewrite_insert_targets(sql: str, orig_name: str, final_name: str) -> str:
  """
  Rewrite every 'INSERT INTO <orig_name>' occurrence to 'INSERT INTO `<final_name>`'.
  Preserves spacing and everything after the target identifier.
  """
  pat = re.compile(_INS_INTO_TARGET_RE_TMPL.format(name=re.escape(orig_name)))
  return pat.sub(r"\1`" + final_name + "`", sql)

def _split_sql_statements(sql: str):
  parts, buf = [], []
  in_s = in_d = in_line_comment = in_block_comment = False
  i, n = 0, len(sql)

  while i < n:
    ch = sql[i]
    nxt = sql[i+1] if i+1 < n else ""

    if in_line_comment:
      if ch == "\n":
        in_line_comment = False
        buf.append(ch)
      i += 1
      continue

    if in_block_comment:
      if ch == "*" and nxt == "/":
        in_block_comment = False
        i += 2
      else:
        i += 1
      continue

    if not in_s and not in_d:
      if ch == "-" and nxt == "-":
        in_line_comment = True
        i += 2
        continue
      if ch == "/" and nxt == "*":
        in_block_comment = True
        i += 2
        continue

    if ch == "'" and not in_d:
      in_s = not in_s
      buf.append(ch); i += 1; continue
    if ch == '"' and not in_s:
      in_d = not in_d
      buf.append(ch); i += 1; continue

    if ch == ";" and not in_s and not in_d:
      stmt = "".join(buf).strip()
      if stmt:
        parts.append(stmt)
      buf = []
      i += 1
      continue

    buf.append(ch); i += 1

  tail = "".join(buf).strip()
  if tail:
    parts.append(tail)
  return parts

def _strip_leading_comments(sql: str) -> str:
  """
  Remove leading whitespace and SQL comments (-- ... and /* ... */) from the given SQL string.
  """
  return _LEADING_COMMENTS_RE.sub("", sql, count=1).lstrip()

def _drop_all_prefixed_tables(cur) -> int:
  like = f"{DB_PREFIX}\\_%"
  cur.execute(
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = DATABASE()
      AND table_name LIKE %s
      AND table_type = 'BASE TABLE'
    """,
    (like,),
  )
  rows = cur.fetchall()
  to_drop = [r[0] if isinstance(r, (list, tuple)) else r["table_name"] for r in rows]

  dropped = 0
  for name in to_drop:
    # No IF EXISTS on purpose (fail loud if enumeration and DB diverge)
    cur.execute(f"DROP TABLE `{name}`")
    logger.info("  - Dropped table `%s`", name)
    dropped += 1
  return dropped

def _get_table_columns(cur, table_name: str) -> list[str]:
  """
  Return the column names for `table_name` in ordinal position order.
  """
  cur.execute(
    """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = %s
    ORDER BY ordinal_position
    """,
    (table_name,),
  )
  rows = cur.fetchall()
  cols = [r[0] if isinstance(r, (list, tuple)) else r["column_name"] for r in rows]
  if not cols:
    raise RuntimeError(f"No columns found for table `{table_name}`")
  return cols

def _wrap_select_as_insert(cur, select_sql: str, final_name: str) -> str:
  """
  Build: INSERT INTO `<final_name>` (`c1`,`c2`,...) <select_sql>
  Column list is pulled live from information_schema for the *target* table.
  """
  cols = _get_table_columns(cur, final_name)
  col_list = ", ".join(f"`{c}`" for c in cols)
  return f"INSERT INTO `{final_name}` ({col_list})\n{select_sql}"

def _exec_insert_and_rowcount(cur, insert_sql: str) -> int:
  """
  STRICT two-step: execute INSERT (or INSERT ... SELECT), then immediately read ROW_COUNT().
  No multi-statements, no COUNT(*) fallback.
  """
  cur.execute(insert_sql)
  cur.execute("SELECT ROW_COUNT() AS rc")
  row = cur.fetchone()
  return int(row.get("rc") if isinstance(row, dict) else row[0])

def _create_and_seed_tables_from_files(cur):
  created = 0
  total_seeded = 0

  files = sorted(glob.glob(os.path.join(TABLES_SQL_DIR, "*.sql")))
  if not files:
    logger.info("No table SQL files found in %s", TABLES_SQL_DIR)
    return 0, 0

  for path in files:
    with open(path, "r", encoding="utf-8") as f:
      sql = f.read()

    m = _HDR_RE.search(sql)
    if not m:
      raise ValueError(f"No CREATE TABLE <name> found in {path}")
    orig_name = m.group(1)
    final_name = _prefixed(orig_name)

    # 1) Rewrite the CREATE header
    sql = _CREATE_RE.sub(r"\1`" + final_name + "`", sql, count=1)
    # 2) Rewrite any explicit INSERT INTO targets (for data files)
    sql = _rewrite_insert_targets(sql, orig_name, final_name)

    statements = _split_sql_statements(sql)
    if not statements:
      continue

    logger.info("  - Creating `%s` from %s", final_name, os.path.basename(path))
    seen_create = False
    seeded_this_table = 0

    for stmt in statements:
      lead = _strip_leading_comments(stmt)
      upper = lead.upper()

      if upper.startswith("CREATE TABLE"):
        cur.execute(stmt)
        created += 1
        seen_create = True
        continue

      if upper.startswith("INSERT INTO"):
        seeded_this_table += max(0, _exec_insert_and_rowcount(cur, stmt))
        continue

      if upper.startswith("SELECT") and seen_create:
        insert_stmt = _wrap_select_as_insert(cur, lead, final_name)
        seeded_this_table += max(0, _exec_insert_and_rowcount(cur, insert_stmt))
        continue

      # Fallback: execute any other DDL/DML as-is
      cur.execute(stmt)

    total_seeded += seeded_this_table
    logger.info("    -> Seeded `%s` (%d rows)", final_name, seeded_this_table)

  return created, total_seeded

def initializeTables(db):
  with db.cursor() as cur:
    logger.info("Dropping tables...")
    dropped = _drop_all_prefixed_tables(cur)
    logger.info("Creating tables...")
    created, total_seeded = _create_and_seed_tables_from_files(cur)
    db.commit()
  logger.info(
    "Tables sync complete: dropped=%d, created=%d, seeded_rows=%d.",
    dropped, created, total_seeded
  )
