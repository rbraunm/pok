from applogging import get_logger
from db import DB_PREFIX
import os
import glob
import re

logger = get_logger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWS_SQL_DIR = os.path.join(HERE, "views")

# Strip any number of leading comments and whitespace:
#  - line comments: -- ... (to end of line)
#  - block comments: /* ... */
_LEADING_COMMENTS_RE = re.compile(
  r"^\s*(?:(?:--[^\n]*\n)|(?:/\*.*?\*/\s*))*",
  flags=re.DOTALL | re.MULTILINE
)

def _strip_leading_comments(sql: str) -> str:
  return _LEADING_COMMENTS_RE.sub("", sql, count=1).lstrip()

def _prefixed(name: str) -> str:
  pref = f"pok_"
  return name if name.startswith(pref) else f"{pref}{name}"

def _sanitize_basename(basename: str) -> str:
  """
  Keep only [A-Za-z0-9_] in the base view name. Convert hyphens/dots to underscores.
  """
  base = os.path.splitext(basename)[0]
  base = re.sub(r"[^A-Za-z0-9_]", "_", base)
  if not base:
    raise ValueError(f"Invalid view filename '{basename}' (empty base after sanitization)")
  return base

def _iter_sql_files():
  return sorted(glob.glob(os.path.join(VIEWS_SQL_DIR, "*.sql")))

def _drop_all_prefixed_views(cur) -> int:
  like = f"{DB_PREFIX}\\_%"
  # Only pull actual views; INFORMATION_SCHEMA.VIEWS excludes tables by definition
  cur.execute(
    """
    SELECT TABLE_NAME
      FROM INFORMATION_SCHEMA.VIEWS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME LIKE %s
    """,
    (like,),
  )
  rows = cur.fetchall()
  names = []
  for row in rows:
    if isinstance(row, dict):
      name = row.get("TABLE_NAME") or row.get("table_name")
    else:
      name = row[0] if row else None
    if name:
      names.append(name)

  if not names:
    logger.info("  - No prefixed views to drop.")
    return 0

  dropped = 0
  for vw in names:
    # Fail loud if enumeration and DB diverge (no IF EXISTS)
    logger.info("  - Dropping view `%s`", vw)
    cur.execute(f"DROP VIEW `{vw}`")
    dropped += 1

  return dropped

def _create_views_from_files(cur) -> int:
  files = _iter_sql_files()
  created = 0

  for path in files:
    with open(path, "r", encoding="utf-8") as f:
      raw_sql = f.read()

    body = _strip_leading_comments(raw_sql)

    if not body:
      raise ValueError(f"Empty view file: {path}")

    # Must start with SELECT (after stripping comments)
    if not body.upper().startswith("SELECT"):
      snippet = body[:160].replace("\n", "\\n")
      raise ValueError(
        f"View files must contain a single SELECT. Offending file: {path}. First 160 chars: {snippet!r}"
      )

    # Normalize end: ensure exactly one semicolon
    body = body.rstrip()
    if body.endswith(";"):
      body = body[:-1].rstrip()

    base = _sanitize_basename(os.path.basename(path))
    final_name = _prefixed(base)

    create_sql = f"CREATE VIEW `{final_name}` AS\n{body};"

    cur.execute(create_sql)
    logger.info("  - Created view `%s`", final_name)
    created += 1

  return created

def initializeViews(db):
  with db.cursor() as cur:
    logger.info("Dropping views...")
    dropped = _drop_all_prefixed_views(cur)
    logger.info("Creating views...")
    created = _create_views_from_files(cur)
    db.commit()
  logger.info("Views sync complete: dropped=%d, created=%d.", dropped, created)
