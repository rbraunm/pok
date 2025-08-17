from __future__ import annotations

import json
from typing import Any, Dict
from flask import render_template
from decimal import Decimal
import datetime
from urllib.parse import urlencode
from applogging import get_logger
logger = get_logger(__name__)

NAV_LINKS: list[tuple[str, str]] = []

def registerNavLink(name: str, url: str) -> None:
    NAV_LINKS.append((name, url))
    NAV_LINKS.sort(key=lambda x: x[0].lower())

def renderNav() -> str:
    linksHtml = "".join(f'<li><a href="{url}">{name}</a></li>' for name, url in NAV_LINKS)
    return f'<ul class="navbar">{linksHtml}</ul>'

def renderPage(header: str | None = None, body: str | None = None) -> str:
    nav = renderNav()
    return render_template("base.html", nav=nav, header=header or "", body=body or "")

def renderPagination(
    currentPage: int,
    totalPages: int,
    baseUrl: str,
    originalParams: dict[str, Any],
    maxVisible: int = 7
) -> str:
    if totalPages <= 1:
        return ""

    def buildUrl(pageNum: int) -> str:
        # Copy params so we don't mutate the original dict
        params: dict[str, Any] = {}
        for k, v in originalParams.items():
            params[k] = list(v) if isinstance(v, list) else v

        params['page'] = pageNum
        params.pop('offset', None)
        qs = urlencode(params, doseq=True)
        return f"{baseUrl}?{qs}#results"

    links: list[str] = ['<nav class="pagination">']

    # Prev link
    if currentPage > 1:
        links.append(f'<a href="{buildUrl(currentPage - 1)}">Prev</a>')
    else:
        links.append('<span class="disabled">Prev</span>')

    # Page number links
    sideSpan = maxVisible // 2
    startPage = max(1, currentPage - sideSpan)
    endPage   = min(totalPages, currentPage + sideSpan)

    if startPage > 1:
        links.append(f'<a href="{buildUrl(1)}">1</a>')
        if startPage > 2:
            links.append('<span class="ellipsis">...</span>')

    for pageNum in range(startPage, endPage + 1):
        cssClass = "active" if pageNum == currentPage else ""
        links.append(f'<a class="{cssClass}" href="{buildUrl(pageNum)}">{pageNum}</a>')

    if endPage < totalPages:
        if endPage < totalPages - 1:
            links.append('<span class="ellipsis">...</span>')
        links.append(f'<a href="{buildUrl(totalPages)}">{totalPages}</a>')

    # Next link
    if currentPage < totalPages:
        links.append(f'<a href="{buildUrl(currentPage + 1)}">Next</a>')
    else:
        links.append('<span class="disabled">Next</span>')

    links.append('</nav>')
    return " ".join(links)

class PoKJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def getNameFromBitmask(value: int, mapping: Dict[str, int]) -> str:
  for name, bit in mapping.items():
    if bit == (1 << (value - 1)):
      return name
  return f"Unknown ({value})"
