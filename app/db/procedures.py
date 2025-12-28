from applogging import get_logger
from db import DB_PREFIX
import os
import glob
import re
from typing import List, Any, Iterable, Tuple

logger = get_logger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
PROCEDURES_SQL_DIR = os.path.join(HERE, "procedures")

# Matches:
#   CREATE PROCEDURE `name`
#   CREATE DEFINER=`user`@`host` PROCEDURE `name`
_PROC_HDR_RE = re.compile(
  r"CREATE\s+"
  r"(?:(?:DEFINER=`[^`]+`@`[^`]+`)\s+)?"
  r"PROCEDURE\s+`?([A-Za-z0-9_]+)`?",
  flags=re.IGNORECASE,
)


def _expected_prefix() -> str:
  return f"{DB_PREFIX}_"


def _row_value(row: Any, name: str, index: int):
  """Helper to support both dict- and tuple-style cursor rows."""
  if isinstance(row, dict):
    return row.get(name)
  return row[index]


def _get_prefixed_procedures(cur) -> List[str]:
  """Return a list of procedure names with our prefix in the current DB."""
  prefix = _expected_prefix()
  cur.execute(
    """
    SELECT
      ROUTINE_NAME AS name
    FROM information_schema.routines
    WHERE ROUTINE_SCHEMA = DATABASE()
      AND ROUTINE_TYPE = 'PROCEDURE'
      AND ROUTINE_NAME LIKE %s
    """,
    (prefix + '%',),
  )
  rows = cur.fetchall() or []
  result: List[str] = []
  for row in rows:
    name = _row_value(row, 'name', 0)
    if name:
      result.append(str(name))
  return result


def _drop_all_prefixed_procedures(cur) -> int:
  """Drop all procedures whose name starts with DB_PREFIX_.

  Returns the number of procedures dropped.
  """
  procedures = _get_prefixed_procedures(cur)
  dropped = 0

  for name in procedures:
    stmt = f"DROP PROCEDURE IF EXISTS `{name}`"
    logger.info("  - Dropping procedure `%s`", name)
    cur.execute(stmt)
    dropped += 1

  return dropped


def _parse_procedures_from_sql(sql_text: str) -> List[str]:
  """Find all procedure names in a SQL file."""
  names: List[str] = []
  for match in _PROC_HDR_RE.finditer(sql_text):
    name = match.group(1)
    if name:
      names.append(name)
  return names


def _validate_procedure_prefix(proc_names: Iterable[str]) -> None:
  """Ensure all procedures have the expected DB prefix.

  Raises ValueError if any name does not match.
  """
  prefix = _expected_prefix()
  bad: List[str] = []
  for name in proc_names:
    if not name.startswith(prefix):
      bad.append(f"`{name}` (expected prefix `{prefix}`)")

  if bad:
    msg = "Found procedures without expected prefix: " + ", ".join(bad)
    logger.error(msg)
    raise ValueError(msg)


def _execute_sql_script(cur, sql_text: str) -> None:
  """Execute a SQL script that may contain DELIMITER directives.

  This is enough for procedure files that look like:

    DELIMITER $$
    CREATE PROCEDURE ...
    BEGIN
      ...
    END$$
    DELIMITER ;

  We update the delimiter client-side and split statements accordingly.
  """
  delimiter = ';'
  buf_lines: List[str] = []

  def flush_buffer():
    nonlocal buf_lines
    if not buf_lines:
      return
    statement = "\n".join(buf_lines).strip()
    if not statement:
      buf_lines = []
      return
    logger.debug("Executing SQL statement (%d chars)", len(statement))
    cur.execute(statement)
    buf_lines = []

  for raw_line in sql_text.splitlines():
    line = raw_line.rstrip("\n")
    stripped = line.strip()

    # Handle DELIMITER directives (client-side only)
    if stripped.upper().startswith("DELIMITER"):
      parts = stripped.split()
      if len(parts) >= 2:
        delimiter = parts[1]
        logger.debug("SQL script delimiter changed to %r", delimiter)
      else:
        logger.warning("Malformed DELIMITER directive: %r", line)
      # Do not include DELIMITER line in the statement buffer
      continue

    buf_lines.append(line)
    current = "\n".join(buf_lines)

    if current.rstrip().endswith(delimiter):
      trimmed = current.rstrip()
      trimmed = trimmed[: -len(delimiter)]
      buf_lines = [trimmed]
      flush_buffer()

  # Any trailing content without a delimiter
  flush_buffer()


def _iter_procedure_files() -> List[str]:
  """Return sorted list of *.sql files in the procedures directory."""
  if not os.path.isdir(PROCEDURES_SQL_DIR):
    logger.warning("Procedures directory does not exist: %s", PROCEDURES_SQL_DIR)
    return []
  pattern = os.path.join(PROCEDURES_SQL_DIR, "*.sql")
  files = sorted(glob.glob(pattern))
  return files


def _create_procedures_from_files(cur) -> int:
  """Create all procedures from .sql files in PROCEDURES_SQL_DIR.

  Supports:
    - One-procedure-per-file style
    - Many-procedures-per-file style
  """
  files = _iter_procedure_files()
  if not files:
    logger.info("No procedure SQL files found in %s", PROCEDURES_SQL_DIR)
    return 0

  expected_prefix = _expected_prefix()
  logger.info("Using DB procedure prefix: %s", expected_prefix)

  total_created = 0

  for path in files:
    logger.info("Processing procedures file: %s", os.path.basename(path))
    with open(path, "r", encoding="utf-8") as f:
      sql_text = f.read()

    proc_names = _parse_procedures_from_sql(sql_text)
    if not proc_names:
      logger.warning("  - No CREATE PROCEDURE statements found in %s", path)
    else:
      _validate_procedure_prefix(proc_names)
      for name in proc_names:
        logger.info("  - Will ensure procedure `%s` is created from this file", name)

    _execute_sql_script(cur, sql_text)
    total_created += len(proc_names)

  return total_created


def initializeProcedures(db):
  """Drop all prefixed procedures and recreate from procedures/*.sql."""
  with db.cursor() as cur:
    logger.info("Dropping procedures with prefix %r...", _expected_prefix())
    dropped = _drop_all_prefixed_procedures(cur)
    logger.info("Creating procedures from SQL files...")
    created = _create_procedures_from_files(cur)
    db.commit()
  logger.info(
    "Procedures sync complete: dropped=%d, created=%d.",
    dropped,
    created,
  )
