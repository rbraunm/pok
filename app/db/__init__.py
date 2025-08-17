# db/__init__.py
# Re-export core DB helpers for convenience. No side effects here.
from .db import getDb, initializeDbObjects, DB_PREFIX
from applogging import get_logger
logger = get_logger(__name__)
