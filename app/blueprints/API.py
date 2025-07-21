NAME = "API"

from flask import json
from api.models.items import get_item, get_item_drops
from api.models.spells import get_spell
from api.models.npcs import get_npc

URL_PREFIX = "/api"

def register(app):
  @app.route(f"{URL_PREFIX}/item/<int:itemId>", methods=["GET"])
  def api_item(itemId):
    return json.dumps(get_item(itemId))

  @app.route(f"{URL_PREFIX}/item/<int:itemId>/drops", methods=["GET"])
  def api_item_drops(itemId):
    return json.dumps(get_item_drops(itemId))


  @app.route(f"{URL_PREFIX}/spell/<int:spellId>", methods=["GET"])
  def api_spell(spellId):
    return json.dumps(get_spell(spellId))


  @app.route(f"{URL_PREFIX}/npc/<int:npcId>", methods=["GET"])
  def api_npc(npcId):
    return json.dumps(get_npc(npcId))
