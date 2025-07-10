NAME = "Data Dump"
URL_PREFIX = "/datadump"

from flask import jsonify, render_template_string
from db import getDb
import json

TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Data Dump</title>
    <style>
      body { font-family: monospace; background: #2c3e50; color: #ecf0f1; margin: 2rem; }
      h1 { margin-bottom: 1rem; }
      .container { position: relative; }
      pre {
        background: #1e272e;
        color: #dff9fb;
        padding: 1rem;
        border-radius: 0.5rem;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        max-height: 80vh;
      }
      button.copy-btn {
        position: absolute;
        top: 0;
        right: 0;
        margin: 1rem;
        background: #1abc9c;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        cursor: pointer;
      }
      button.copy-btn:hover {
        background: #16a085;
      }
    </style>
  </head>
  <body>
    <h1>Data Dump (first 100 rows per table)</h1>
    <div class="container">
      <button class="copy-btn" onclick="copyJSON()">Copy JSON</button>
      <pre id="jsonOutput">{{ data }}</pre>
    </div>

    <script>
      function copyJSON() {
        const pre = document.getElementById("jsonOutput");
        navigator.clipboard.writeText(pre.innerText).then(() => {
          alert("JSON copied to clipboard.");
        });
      }
    </script>
  </body>
</html>
"""

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def datadump():
    db = getDb()
    result = {}

    tables = [
      "items",
      "zone",
      "npc_types",
      "spawnentry",
      "spawn2",
      "loottable",
      "loottable_entries",
      "lootdrop_entries"
    ]

    with db.cursor() as cur:
      for table in tables:
        cur.execute(f"SELECT * FROM {table} LIMIT 100")
        result[table] = cur.fetchall()

    return render_template_string(TEMPLATE, data=json.dumps(result, indent=2))
