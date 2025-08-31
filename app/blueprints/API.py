NAME = "API"

from flask import json, Response
from applogging import get_logger
logger = get_logger(__name__)

# --- Models (data) ---
from api.models.items import get_item
from api.models.npcs import get_npc, get_item_drops, get_item_merchants
from api.models.spells import get_spell
from api.models.tradeskill import get_item_recipes

# --- Renderers (HTML) ---
from api.renderers.items import render_item_header
from api.renderers.npcs import render_item_drops, render_item_merchants
from api.renderers.tradeskill import render_recipe_list

URL_PREFIX = "/api"

def _html(s: str) -> Response:
  return Response(s or "", mimetype="text/html; charset=utf-8")

def register(app):
  # ------------------------------
  # JSON endpoints
  # ------------------------------
  @app.route(f"{URL_PREFIX}/item/<int:itemId>", methods=["GET"])
  def api_item(itemId):
    return json.dumps(get_item(itemId))

  @app.route(f"{URL_PREFIX}/item/<int:itemId>/drops", methods=["GET"])
  def api_item_drops(itemId):
    return json.dumps(get_item_drops(itemId))

  @app.route(f"{URL_PREFIX}/item/<int:itemId>/merchants", methods=["GET"])
  def api_item_merchants(itemId):
    return json.dumps(get_item_merchants(itemId))

  @app.route(f"{URL_PREFIX}/item/<int:itemId>/recipes", methods=["GET"])
  def api_item_recipes(itemId):
    return json.dumps(get_item_recipes(itemId))

  @app.route(f"{URL_PREFIX}/spell/<int:spellId>", methods=["GET"])
  def api_spell(spellId):
    return json.dumps(get_spell(spellId))

  @app.route(f"{URL_PREFIX}/npc/<int:npcId>", methods=["GET"])
  def api_npc(npcId):
    return json.dumps(get_npc(npcId))

  # -----------------------------------
  # HTML endpoints
  # -----------------------------------

  # Header-only (useful for compact cards / tooltips)
  @app.route(f"{URL_PREFIX}/render/item/<int:itemId>/header", methods=["GET"])
  def api_render_item_header(itemId):
    try:
      item = get_item(itemId) or {}
      return _html(render_item_header(item))
    except Exception:
      logger.exception("Exception in API render(item/header)")
      return _html("<div class='error'>Failed to render item header.</div>")

  # Drops-only section (delegates to renderers.npcs)
  @app.route(f"{URL_PREFIX}/render/item/<int:itemId>/drops", methods=["GET"])
  def api_render_item_drops(itemId):
    try:
      drops = get_item_drops(itemId) or []
      return _html(render_item_drops(drops))
    except Exception:
      logger.exception("Exception in API render(item/drops)")
      return _html("<div class='error'>Failed to render drops.</div>")

  # Merchants-only section (delegates to renderers.npcs)
  @app.route(f"{URL_PREFIX}/render/item/<int:itemId>/merchants", methods=["GET"])
  def api_render_item_merchants(itemId):
    try:
      merchants = get_item_merchants(itemId) or []
      return _html(render_item_merchants(merchants))
    except Exception:
      logger.exception("Exception in API render(item/merchants)")
      return _html("<div class='error'>Failed to render merchants.</div>")

  # Recipes-only section (delegates to renderers.tradeskill)
  @app.route(f"{URL_PREFIX}/render/item/<int:itemId>/recipes", methods=["GET"])
  def api_render_item_recipes_html(itemId):
    try:
      recipes = get_item_recipes(itemId) or []
      return _html(render_recipe_list(recipes))
    except Exception:
      logger.exception("Exception in API render(item/recipes)")
      return _html("<div class='error'>Failed to render recipes.</div>")

  # One-shot "details" panel (header + drops + merchants + recipes)
  @app.route(f"{URL_PREFIX}/render/item/<int:itemId>/details", methods=["GET"])
  def api_render_item_details(itemId):
    try:
      item = get_item(itemId) or {}
      drops = get_item_drops(itemId) or []
      merchants = get_item_merchants(itemId) or []
      recipes = get_item_recipes(itemId) or []

      head_html = render_item_header(item)
      drops_html = render_item_drops(drops)
      merch_html = render_item_merchants(merchants)
      recs_html  = render_recipe_list(recipes)

      # Simple section wrappers match your current styling approach
      return _html(
        "<div class='gs-item-details'>"
        f"  {head_html}"
        f"  <section class='gs-subsection'><h4>Drops</h4>{drops_html or '<p class=\"muted\">No known drops.</p>'}</section>"
        f"  <section class='gs-subsection'><h4>Merchants</h4>{merch_html or '<p class=\"muted\">No merchants found.</p>'}</section>"
        f"  <section class='gs-subsection'><h4>Recipes</h4>{recs_html or '<p class=\"muted\">No recipes found.</p>'}</section>"
        "</div>"
      )
    except Exception:
      logger.exception("Exception in API render(item/details)")
      return _html("<div class='error'>Failed to render item details.</div>")
