from __future__ import annotations

import html
from typing import Dict, Any
from applogging import get_logger
from web.utils import getNameFromBitmask
from api.models.characters import CLASS_BITMASK, RACE_BITMASK

logger = get_logger(__name__)

def render_character_summary(character: Dict[str, Any]) -> str:
  """Return the character summary panel HTML (portrait + basic facts)."""
  if not character:
    return ""
  try:
    className = getNameFromBitmask(character['class_id'], CLASS_BITMASK).lower()
    raceName = getNameFromBitmask(character['race_id'], RACE_BITMASK)
  except Exception as e:
    logger.exception("Failed to render character summary: %s", e)
    return ""
  return f"""
    <div class="character-summary">
      <img src="/static/img/class_portraits/{className}.gif" alt="{className} portrait" class="class-portrait" />
      <div class="character-details">
        <h2>{html.escape(character['name'])}</h2>
        <p>Class: {className.title()}<br>
        Level: {character['level']}<br>
        Race: {raceName}</p>
      </div>
    </div>
  """
