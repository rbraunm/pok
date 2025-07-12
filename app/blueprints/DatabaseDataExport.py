NAME = "Database Data Export"

from pathlib import Path
URL_PREFIX = "/" + Path(__file__).stem.lower()

from flask import Response
from api.models.exports import sample_tables
from api.models.schema import list_tables
from app import renderPage
import json

def register(app):
  @app.route(URL_PREFIX)
  def dataExport():
    tables    = list_tables()
    data      = sample_tables(tables, limit=100)
    jsonData  = json.dumps(data, default=str, indent=2)

    header = f"""
<div class="headerRow">
  <h1>{NAME}</h1>
  <button class="download-btn" onclick="downloadJSON()">Download JSON</button>
</div>"""

    body  = f"<pre>{jsonData}</pre>" + """
<script>
function downloadJSON() {
  const data = document.querySelector('pre')?.innerText;
  if (!data) return;
  const blob  = new Blob([data], {type: 'application/json'});
  const url   = URL.createObjectURL(blob);
  const a     = document.createElement('a');
  a.href      = url;
  a.download  = 'pok-data-export.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
</script>"""
    return renderPage(header, body)

  @app.route(f"{URL_PREFIX}/raw")
  def dataExportRaw():
    tables = list_tables()
    data   = sample_tables(tables, limit=100)
    return Response(json.dumps(data, default=str),
                    mimetype="application/json")
