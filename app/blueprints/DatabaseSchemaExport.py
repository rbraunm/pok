NAME = "Database Schema Export"

from pathlib import Path
URL_PREFIX = "/" + Path(__file__).stem.lower()

from flask import Response
from api.models.schema import list_tables, describe_table
from app import renderPage
import json

def register(app):
  @app.route(URL_PREFIX)
  def schemaTables():
    tables  = list_tables()
    header  = f"""
<div class="headerRow">
  <h1>{NAME}</h1>
  <button class="download-btn" onclick="downloadAll()">Download JSON</button>
</div>"""
    
    body    = "<ul>" + "".join(
      f"<li><a href='{URL_PREFIX}/{t}'>{t}</a></li>" for t in tables
    ) + "</ul>" + """
<script>
function downloadAll() {
  fetch(window.location.pathname + '/raw')
    .then(r => r.text())
    .then(txt => {
      const blob = new Blob([txt], {type:'application/json'});
      const url  = URL.createObjectURL(blob);
      const a    = Object.assign(document.createElement('a'), {
        href:url, download:'pok-schema-all.json'
      });
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    });
}
</script>"""
    return renderPage(header, body)

  @app.route(f"{URL_PREFIX}/raw")
  def schemaRaw():
    data = {t: describe_table(t) for t in list_tables()}
    return Response(json.dumps(data, default=str, indent=2),
                    mimetype="application/json")

  @app.route(f"{URL_PREFIX}/<table>")
  def schemaTable(table):
    cols   = describe_table(table)
    header = f"""
<div class="headerRow">
  <h1>Schema for {table}</h1>
  <button class="download-btn" onclick="downloadTable()">Download JSON</button>
</div>"""
    body   = "<pre>" + json.dumps(cols, default=str, indent=2) + "</pre>" + """
<script>
function downloadTable() {
  fetch(window.location.pathname + '/raw')
    .then(r => r.text())
    .then(txt => {
      const blob = new Blob([txt], {type:'application/json'});
      const url  = URL.createObjectURL(blob);
      const a    = Object.assign(document.createElement('a'), {
        href:url, download:`pok-schema-${window.location.pathname.split('/').pop()}.json`
      });
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    });
}
</script>"""
    return renderPage(header, body)

  @app.route(f"{URL_PREFIX}/<table>/raw")
  def schemaTableRaw(table):
    return Response(json.dumps(describe_table(table), default=str, indent=2),
                    mimetype="application/json")
