import logging
from applogging import get_logger

# Initialize your app's logging ea`rly in the master
get_logger("gunicorn.bootstrap")

try:
  from gunicorn.glogging import Logger  # type: ignore[import]
except Exception:
  class Logger:  # fallback for local editors without gunicorn installed
    def setup(self, cfg): pass

class AppLogger(Logger):
  def setup(self, cfg):
    try:
      super().setup(cfg)
    except Exception:
      pass
    # Route Gunicorn logs through your app_logging handlers/format
    for name in ("gunicorn.error", "gunicorn.access"):
      lg = logging.getLogger(name)
      lg.handlers.clear()
      lg.propagate = True

logger_class = AppLogger

# Ensure print()/stdout/stderr from workers get your formatter too
capture_output = True
