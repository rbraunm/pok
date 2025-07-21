NAME = "Spell Book"

from pathlib import Path
import html
from flask import request
from web.utils import renderPage
from api.models.characters import search_characters, get_character
from api.models.spells import get_spells_for_character

URL_PREFIX = "/" + Path(__file__).stem

def group_spells_by_level(spells):
  grouped = {}
  for spell in spells:
    level = spell.get("spelllevel", 0) or 0
    grouped.setdefault(level, []).append(spell)
  
  for level in grouped:
    grouped[level].sort(key=lambda s: s["name"])

  return dict(sorted(grouped.items()))

def render_character_summary(character):
  return (
    f"<h2>{html.escape(character['name'])}</h2>"
    f"<p>Class: {character['class']}<br>"
    f"Level: {character['level']}<br>"
    f"Race: {character['race']}<br>"
    f"Deity: {character['deity']}</p>"
  )

def render_spell_list(grouped_spells):
  parts = []
  for level, spells in grouped_spells.items():
    parts.append(f"<h3>Level {level}</h3>")
    parts.append("<ul>")
    for spell in spells:
      parts.append(f"<li>{html.escape(spell['name'])} (Mana: {spell['mana']}, Resist: {spell['resisttype']})</li>")
    parts.append("</ul>")
  return "\n".join(parts)

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def spellbook():
    char_query = request.args.get("character", "").strip()
    char_id = request.args.get("charId")
    htmlContent = ""
    if char_query:
      results = search_characters(char_query)
      htmlContent += "<h2>Character Search Results</h2><ul>"
      for c in results:
        htmlContent += (
          f"<li><a href='?charId={c['id']}'>{html.escape(c['name'])} "
          f"(Level {c['level']} {c['class']})</a></li>"
        )
      htmlContent += "</ul>"

    if char_id:
      character = get_character(int(char_id))
      if character:
        spells = get_spells_for_character(character["id"])
        grouped = group_spells_by_level(spells)

        htmlContent += render_character_summary(character)
        htmlContent += render_spell_list(grouped)
      else:
        htmlContent += "<p>Character not found.</p>"

    return renderPage(htmlContent)
