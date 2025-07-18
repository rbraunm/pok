"""
Plane of Knowledge web front-end – circular-safe version
"""
from __future__ import annotations

import datetime as _dt
import html
import importlib.util
import json
import os
import sys
import traceback
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, render_template, request

APP_VERSION = "0.2.1"
POK_DEBUG = os.getenv("POK_DEBUG", "false").lower() == "true"


# --------------------------------------------------------------------------- #
#  Shared helpers – defined EARLY so blueprints can import them safely
# --------------------------------------------------------------------------- #
class PoKJSONEncoder(json.JSONEncoder):
  """Adds ISO-8601 datetime & Decimal → float support."""

  def default(self, obj):  # noqa: D401
    if isinstance(obj, (_dt.date, _dt.datetime)):
      return obj.isoformat()
    if isinstance(obj, Decimal):
      return float(obj)
    return super().default(obj)


def renderPage(header: str = "", body: str = ""):
  """Tiny wrapper around ``base.html`` so blueprints have one-liner pages."""
  return render_template("base.html", header=header, body=body)


# Make the helpers visible even while *this* module is still initialising
sys.modules[__name__].PoKJSONEncoder = PoKJSONEncoder  # type: ignore[attr-defined]
sys.modules[__name__].renderPage = renderPage           # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
#  Dynamic loader
# --------------------------------------------------------------------------- #
def _import_module_from_path(mod_name: str, path: Path):
  spec = importlib.util.spec_from_file_location(mod_name, path)
  if spec is None or spec.loader is None:  # pragma: no cover
    raise ImportError(f"Cannot load module {mod_name} from {path}")
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)  # type: ignore[arg-type]
  return module


def _load_everything(app: Flask) -> tuple[list[dict[str, str]], list[str]]:
  plugin_endpoints: List[Dict[str, str]] = []
  load_errors: List[str] = []

  # Core models --------------------------------------------------------------
  try:
    import api  # noqa: F401  (executes any model singletons)
  except Exception:
    load_errors.append(
      "<h3>Failed to load core models</h3>"
      f"<pre>{html.escape(traceback.format_exc())}</pre>"
    )
    if POK_DEBUG:
      traceback.print_exc()

  # Blueprints ---------------------------------------------------------------
  bp_dir = Path(__file__).with_name("blueprints")
  for py_file in sorted(bp_dir.glob("*.py")):
    mod_name = py_file.stem
    try:
      module = _import_module_from_path(mod_name, py_file)

      if hasattr(module, "register"):                 # legacy helper
        module.register(app)  # type: ignore[arg-type]
        url_prefix = getattr(module, "URL_PREFIX", f"/{mod_name}")
      else:                                          # plain Blueprint export
        bp = getattr(module, "bp", None) or getattr(module, "blueprint", None)
        if bp is None:
          raise AttributeError(
            "Blueprint must export either `register(app)` or a Blueprint "
            "named `bp` / `blueprint`."
          )
        app.register_blueprint(bp)
        url_prefix = getattr(bp, "url_prefix", f"/{mod_name}")

      plugin_endpoints.append(
        {
          "name": getattr(module, "NAME", mod_name.replace('_', ' ').title()),
          "url": url_prefix,
        }
      )

    except Exception:
      load_errors.append(
        f"<h3>Failed to load blueprint: {mod_name}</h3>"
        f"<pre>{html.escape(traceback.format_exc())}</pre>"
      )
      if POK_DEBUG:
        traceback.print_exc()

  plugin_endpoints.sort(key=lambda p: p["name"])
  return plugin_endpoints, load_errors


# --------------------------------------------------------------------------- #
#  Application factory
# --------------------------------------------------------------------------- #
def create_app() -> Flask:
  app = Flask(__name__, static_folder="static", template_folder="templates")
  app.json_encoder = PoKJSONEncoder

  plugin_endpoints, load_errors = _load_everything(app)

  @app.context_processor
  def _inject():
    return dict(plugins=plugin_endpoints, version=APP_VERSION)

  @app.route("/")
  def index():
    body = "<p>Select a tool from the menu on the left.</p>" + "".join(load_errors)
    return renderPage("<h1>Plane of Knowledge</h1>", body)

  # Unified 500 handler that surfaces tracebacks when POK_DEBUG=true
  @app.errorhandler(Exception)
  def _unhandled(_err):
    tb = traceback.format_exc()
    msg = (
      "<h2>Internal Server Error</h2>"
      "<p>An unhandled exception occurred while processing your request.</p>"
      f"<pre>{html.escape(tb)}</pre>"
    )
    load_errors.append(msg)
    if POK_DEBUG:
      print(tb, flush=True)

    if "text/html" in request.accept_mimetypes:
      return renderPage("Error", msg), 500
    return {"error": "internal-server-error"}, 500

  return app


# WSGI entry-point -----------------------------------------------------------
app = create_app()
