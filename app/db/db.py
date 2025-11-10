import json
import pymysql
import pymysql.cursors
from threading import Lock
from applogging import get_logger
logger = get_logger(__name__)

_db = None
_db_lock = Lock()
DB_PREFIX = "pok"

SESSION_TUNING_SQL = [
  "SET SESSION max_heap_table_size=1073741824",
  "SET SESSION tmp_table_size=1073741824",
  "SET SESSION sort_buffer_size=67108864",
  "SET SESSION join_buffer_size=33554432",
  "SET SESSION read_buffer_size=33554432",
  "SET SESSION read_rnd_buffer_size=33554432",
  "SET SESSION group_concat_max_len=131072",
]

def _apply_session_tuning(conn):
  with conn.cursor() as cur:
    for stmt in SESSION_TUNING_SQL:
      cur.execute(stmt)
  conn.commit()

def getConfig():
  with open("/app/server/eqemu_config.json") as f:
    return json.load(f)

def getDb():
  global _db
  with _db_lock:
    cfg = getConfig()["server"]["database"]

    def _connect():
      conn = pymysql.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["username"],
        password=cfg["password"],
        database=cfg["db"],
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
        autocommit=True,
      )
      _apply_session_tuning(conn)
      return conn

    # No connection yet or it's closed → open fresh
    if _db is None or not getattr(_db, "open", False):
      _db = _connect()
      return _db

    # Have a connection: ensure it’s alive; reconnect if needed
    try:
      _db.ping(reconnect=True)
      if not _db.open:
        logger.warning("DB connection not open after ping; reconnecting")
        _db = _connect()
      return _db

    except Exception:
      # Cleanup quietly; let the exception bubble to the global handler
      try:
        if _db and getattr(_db, "open", False):
          _db.close()
      except Exception:
        pass
      _db = None
      raise

def initializeDbObjects():
  logger.info("Initializing database objects...")
  db = getDb()

  from db.indexes import initializeIndexes
  from db.functions import initializeFunctions
  from db.tables import initializeTables
  from db.views import initializeViews

  # Build structure in dependency-safe order
  initializeIndexes(db)
  initializeFunctions(db)
  initializeTables(db)
  initializeViews(db)

  db.commit()
  logger.info("DB initialization completed.")
  db.close()
