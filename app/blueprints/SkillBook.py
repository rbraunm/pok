NAME = "Skill Book"

from pathlib import Path
import html
from flask import request
from web.utils import renderPage, getNameFromBitmask
from api.models.characters import search_characters, get_character, CLASS_BITMASK
from api.models.tradeskill import TRADESKILL, get_skills_by_character, get_skill_up_recipes
from api.renderers.tradeskill import render_recipe_list
from api.renderers.characters import render_character_summary
from applogging import get_logger
logger = get_logger(__name__)

URL_PREFIX = "/" + Path(__file__).stem

def render_tradeskill_list(characterId, tradeskillValues):
  html_parts = ['<div class="tradeskill-list"><h3>Tradeskills</h3><ul>']

  # Sort by tradeskill name
  for skillId, value in sorted(tradeskillValues.items(), key=lambda item: TRADESKILL.get(item[0], "").lower()):
    skillName = TRADESKILL.get(skillId)
    if not skillName:
      continue
    html_parts.append(
      f"<li><a href='?charId={characterId}&skillId={skillId}'>{html.escape(skillName)}: {value}</a></li>"
    )

  html_parts.append("</ul></div>")
  return "\n".join(html_parts)

def render_skill_up_recipes(skillId, characterSkill):
  recipes = get_skill_up_recipes(skillId, characterSkill)
  if not recipes:
    return ""

  html_header = f"<h3>Skill-Up Recipes for {TRADESKILL.get(skillId, 'Unknown')}</h3>"
  return html_header + render_recipe_list(recipes, characterSkill)

def render_search_results(results):
  if not results:
    return "<p>No matching characters found.</p>"
  parts = ["<h2>Character Search Results</h2><ul>"]
  for c in results:
    className = getNameFromBitmask(c['class_id'], CLASS_BITMASK)
    parts.append(
      f"<li><a href='?charId={c['id']}'>{html.escape(c['name'])} "
      f"(Level {c['level']} {className})</a></li>"
    )
  parts.append("</ul>")
  return "\n".join(parts)

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def skillbook():
    char_query = request.args.get("character", "").strip()
    char_id = request.args.get("charId")
    skill_id = request.args.get("skillId", type=int)

    htmlContent = f"""
      <form method="get" action="">
        <label for="character">Search Character:</label>
        <input type="text" id="character" name="character" value="{html.escape(char_query)}" />
        <input type="submit" value="Search" />
      </form>
      <hr>
    """

    if char_query:
      search_results = search_characters(char_query)
      if len(search_results) == 1:
        char_id = search_results[0]["id"]
      else:
        htmlContent += render_search_results(search_results)

    if char_id:
      character = get_character(int(char_id))
      if character:
        tradeskills = get_skills_by_character(character['id'])
        skillUpHtml = ""

        if skill_id in tradeskills:
          skill_value = tradeskills.get(skill_id, 0)
          skillUpHtml = render_skill_up_recipes(skill_id, skill_value)

        leftPanel = render_character_summary(character) + render_tradeskill_list(character['id'], tradeskills)

        htmlContent += f"""
          <div style="display: flex; gap: 40px; align-items: flex-start;">
            <div style="min-width: 220px;">{leftPanel}</div>
            <div style="flex-grow: 1;">{skillUpHtml}</div>
          </div>
        """
      else:
        htmlContent += "<p>Character not found.</p>"

    return renderPage(htmlContent)
