from applogging import get_logger
from db import DB_PREFIX
import os
import glob
import re

logger = get_logger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
FUNCTIONS_SQL_DIR = os.path.join(HERE, "functions")

_HDR_RE = re.compile(r"CREATE\s+FUNCTION\s+`?([A-Za-z0-9_]+)`?", flags=re.IGNORECASE)
_CREATE_RE = re.compile(r"(CREATE\s+FUNCTION\s+)`?[A-Za-z0-9_]+`?", flags=re.IGNORECASE)


def _prefixed(name: str) -> str:
  pref = f"pok_"
  return name if name.startswith(pref) else f"{pref}{name}"


def _rename_to_prefixed(sql: str, orig_name: str) -> str:
  # Replace only the first function name in the CREATE header (case-insensitive)
  return _CREATE_RE.sub(lambda m: f"{m.group(1)}`{_prefixed(orig_name)}`", sql, count=1)


def _iter_sql_files():
  return sorted(glob.glob(os.path.join(FUNCTIONS_SQL_DIR, "*.sql")))


def _drop_all_prefixed_functions(cur) -> int:
  like = f"{DB_PREFIX}\\_%"
  cur.execute(
    """
    SELECT ROUTINE_NAME
      FROM INFORMATION_SCHEMA.ROUTINES
     WHERE ROUTINE_TYPE = 'FUNCTION'
       AND ROUTINE_SCHEMA = DATABASE()
       AND ROUTINE_NAME LIKE %s
    """
    , (like,),
  )
  rows = cur.fetchall()
  names = []
  for row in rows:
    name = row.get("ROUTINE_NAME") or row.get("routine_name")
    if name is None:
      try:
        name = next(iter(row.values()))
      except StopIteration:
        name = None
    if name:
      names.append(name)

  if not names:
    logger.info("  - No prefixed functions to drop.")
    return 0

  dropped = 0
  for fn in names:
    cur.execute(f"DROP FUNCTION `{fn}`")
    logger.info("  - Dropped function `%s`", fn)
    dropped += 1

  return dropped


def _create_functions_from_files(cur) -> int:
  files = _iter_sql_files()
  created = 0
  for path in files:
    with open(path, "r", encoding="utf-8") as f:
      sql = f.read()

    m = _HDR_RE.search(sql)
    if not m:
      snippet = sql[:160].replace("\n", "\\n")
      raise ValueError(f"CREATE FUNCTION header not found in {path}. First 160 chars: {snippet!r}")

    orig_name = m.group(1)
    final_name = _prefixed(orig_name)
    sql = _rename_to_prefixed(sql, orig_name)
    try:
      cur.execute(sql)
    except Exception as e:
      raise e.__class__(f"{e} [function={final_name} file={path}]") from e

    logger.info("  - Created function `%s`", final_name)
    created += 1

  return created


def initializeFunctions(db):
  with db.cursor() as cur:
    logger.info("Dropping functions...")
    dropped = _drop_all_prefixed_functions(cur)
    logger.info("Creating functions...")
    created = _create_functions_from_files(cur)
    db.commit()
  logger.info("Functions sync complete: dropped=%d, created=%d.", dropped, created)
