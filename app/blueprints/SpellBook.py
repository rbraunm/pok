NAME = "Spell Book"

from pathlib import Path
import html
from flask import request
from web.utils import renderPage, getNameFromBitmask
from api.models.characters import search_characters, get_character, CLASS_BITMASK
from api.models.spells import get_spells_for_character
from api.renderers.characters import render_character_summary
from applogging import get_logger
logger = get_logger(__name__)

URL_PREFIX = "/" + Path(__file__).stem

def group_spells_by_level(spells):
  grouped = {}
  for spell in spells:
    level = spell.get("required_level", 0) or 0
    grouped.setdefault(level, []).append(spell)
  for level in grouped:
    grouped[level].sort(key=lambda s: s["name"])
  return dict(sorted(grouped.items(), reverse=True))

def render_spell_list(grouped_spells):
  parts = []
  for level, spells in grouped_spells.items():
    parts.append(f"<div class='spell-level-block'>")
    parts.append(f"<h4 class='spell-level-title'>Level {level}</h4>")
    parts.append("<ul class='spell-list'>")
    for spell in spells:
      className = "known-spell" if spell.get("known") else "unknown-spell"
      parts.append(
        f"<li class='{className}'>"
        f"<span class='eqtooltip' data-type='spell' data-id='{spell['id']}'>"
        f"{html.escape(spell['name'])}</span></li>"
      )
    parts.append("</ul></div>")
  return "\n".join(parts)

def render_search_results(results):
  known_param = request.args.get("known", "all")  
  if not results:
    return "<p>No matching characters found.</p>"
  parts = ["<h2>Character Search Results</h2><ul>"]
  for c in results:
    className = getNameFromBitmask(c['class_id'], CLASS_BITMASK)
    parts.append(
      f"<li><a href='?charId={c['id']}&known={known_param}'>{html.escape(c['name'])} "
      f"(Level {c['level']} {className})</a></li>"
    )
  parts.append("</ul>")
  return "\n".join(parts)

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def spellbook():
    char_query = request.args.get("character", "").strip()
    char_id = request.args.get("charId")
    known_filter = request.args.get("known", "all").strip().lower()

    htmlContent = f"""
      <form method="get" action="">
        <label for="character">Search Character:</label>
        <input type="text" id="character" name="character" value="{html.escape(char_query)}" />

        <label for="known">Show:</label>
        <select name="known" id="known">
          <option value="all" {"selected" if known_filter == "all" else ""}>All Spells</option>
          <option value="yes" {"selected" if known_filter == "yes" else ""}>Known Only</option>
          <option value="no" {"selected" if known_filter == "no" else ""}>Unknown Only</option>
        </select>

        <input type="submit" value="Search" />
      </form>
      <hr>
    """

    # If searching by name
    if char_query:
      search_results = search_characters(char_query)

      # If only one result, auto-select it
      if len(search_results) == 1:
        char_id = search_results[0]["id"]
      else:
        htmlContent += render_search_results(search_results)


    # If character ID is provided, show their spells
    if char_id:
      character = get_character(int(char_id))
      if character:
        all_spells = get_spells_for_character(character["id"])
        if known_filter == "yes":
          spells = [s for s in all_spells if s.get("known")]
        elif known_filter == "no":
          spells = [s for s in all_spells if not s.get("known")]
        else:
          spells = all_spells
        grouped = group_spells_by_level(spells)
        leftPanel = render_character_summary(character)
        rightPanel = render_spell_list(grouped)

        htmlContent += f"""
          <div style="display: flex; gap: 40px; align-items: flex-start;">
            <div style="min-width: 220px;">{leftPanel}</div>
            <div style="flex-grow: 1;">{rightPanel}</div>
          </div>
        """

      else:
        htmlContent += "<p>Character not found.</p>"

    return renderPage(htmlContent)
