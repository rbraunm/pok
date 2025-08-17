import logging
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# ---------- custom levels ----------
TRACE = 5
SUCCESS = 25
logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(SUCCESS, "SUCCESS")

_LEVEL_ALIASES = {
  "trace": TRACE,
  "debug": logging.DEBUG,
  "info": logging.INFO,
  "success": SUCCESS,
  "warn": logging.WARNING,
  "warning": logging.WARNING,
  "error": logging.ERROR,
  "critical": logging.CRITICAL,
  "fatal": logging.CRITICAL,
  "off": logging.CRITICAL + 10,
  "none": logging.CRITICAL + 10,
}

def _parse_level(value):
  if value is None:
    return logging.INFO
  if isinstance(value, int):
    return value
  s = str(value).strip().lower()
  return _LEVEL_ALIASES.get(s, logging.INFO)

# ---------- timezone ----------
def _resolve_tz() -> ZoneInfo:
  """
  Resolve logging timezone in this order:
    1) POK_LOG_TZ
    2) TZ
    3) UTC
  """
  name = os.environ.get("POK_LOG_TZ") or os.environ.get("TZ") or "UTC"
  try:
    return ZoneInfo(name)
  except Exception:
    return ZoneInfo("UTC")

# ---------- colors (forced on) ----------
RESET = "\x1b[0m"
COLOR_FOR_LEVEL = {
  TRACE:             "\x1b[90m",    # bright black (gray)
  logging.DEBUG:     "\x1b[36m",    # cyan
  logging.INFO:      "\x1b[34m",    # blue
  SUCCESS:           "\x1b[32m",    # green
  logging.WARNING:   "\x1b[33m",    # yellow
  logging.ERROR:     "\x1b[31m",    # red
  logging.CRITICAL:  "\x1b[1;31m",  # bold red
}

class ColorFormatter(logging.Formatter):
  def __init__(self, tzinfo: ZoneInfo):
    super().__init__(fmt="%(message)s")
    self.tzinfo = tzinfo

  def format(self, record: logging.LogRecord) -> str:
    # Millisecond precision, rendered in configured tz
    ts = datetime.fromtimestamp(record.created, self.tzinfo).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    color = COLOR_FOR_LEVEL.get(record.levelno)
    levelname = f"{color}{record.levelname}{RESET}" if color else record.levelname
    where = f"{record.name}:{record.lineno}"
    msg = super().format(record)  # uses record.getMessage()
    return f"{ts} | {levelname:<8} | {where} | {msg}"

class MaxLevelFilter(logging.Filter):
  def __init__(self, max_level: int):
    super().__init__()
    self.max_level = max_level
  def filter(self, record: logging.LogRecord) -> bool:
    return record.levelno < self.max_level

class MinLevelFilter(logging.Filter):
  def __init__(self, min_level: int):
    super().__init__()
    self.min_level = min_level
  def filter(self, record: logging.LogRecord) -> bool:
    return record.levelno >= self.min_level

def _log_trace(self, msg, *args, **kwargs):
  if self.isEnabledFor(TRACE):
    self._log(TRACE, msg, args, **kwargs)

def _log_success(self, msg, *args, **kwargs):
  if self.isEnabledFor(SUCCESS):
    self._log(SUCCESS, msg, args, **kwargs)

logging.Logger.trace = _log_trace           # type: ignore[attr-defined]
logging.Logger.success = _log_success       # type: ignore[attr-defined]

# ---------- configuration ----------
_CONFIGURED = False

def configure_logging(level=None) -> None:
  """
  Configure root logger with forced color formatters and stdout/stderr split.
  Safe to call multiple times; subsequent calls update the level.
  """
  global _CONFIGURED
  root = logging.getLogger()
  lvl = _parse_level(level if level is not None else os.environ.get("POK_LOG_LEVEL"))
  tzinfo = _resolve_tz()

  if _CONFIGURED and root.handlers:
    root.setLevel(lvl)
    return

  root.setLevel(lvl)

  out_handler = logging.StreamHandler(sys.stdout)
  err_handler = logging.StreamHandler(sys.stderr)
  out_handler.addFilter(MaxLevelFilter(logging.ERROR))
  err_handler.addFilter(MinLevelFilter(logging.ERROR))

  fmt = ColorFormatter(tzinfo=tzinfo)
  out_handler.setFormatter(fmt)
  err_handler.setFormatter(fmt)

  root.handlers.clear()
  root.addHandler(out_handler)
  root.addHandler(err_handler)
  _CONFIGURED = True

def set_level(level) -> None:
  logging.getLogger().setLevel(_parse_level(level))

def get_logger(name: str | None = None) -> logging.Logger:
  configure_logging()
  return logging.getLogger(name or "pok")

configure_logging()
