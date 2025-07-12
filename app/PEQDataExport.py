NAME = "PEQ Data Export"
URL_PREFIX = "/peqdataexport"

from flask import Response, request, url_for
from db import getDb
from app import renderPage
import pymysql.cursors
import json
import html
import traceback
from datetime import datetime, date

def defaultJsonHandler(obj):
  from decimal import Decimal
  from uuid import UUID
  from datetime import datetime, date

  if isinstance(obj, (datetime, date)):
    return obj.isoformat()
  if isinstance(obj, Decimal):
    return float(obj)
  if isinstance(obj, UUID):
    return str(obj)
  return str(obj)  # fallback: log and return string

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def peqDataExport():
    try:
      db = getDb()
      result = {}

      with db.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();")
        tables = [r["table_name"] for r in cur.fetchall()]

        for table in tables:
          cur.execute(f"SELECT * FROM `{table}` LIMIT 100")
          result[table] = cur.fetchall()

      jsonData = json.dumps(result, indent=2, default=defaultJsonHandler)

      if request.args.get("download") == "1":
        return Response(
          jsonData,
          mimetype="application/json",
          headers={"Content-Disposition": "attachment; filename=PEQDataExport.json"}
        )

      header = f'''
        <div class="headerRow">
          <h1>PEQ Data Export</h1>
          <a class="download-btn" href="{url_for("peqDataExport")}?download=1">Download JSON</a>
        </div>
      '''
      body = f'<pre>{html.escape(jsonData)}</pre>'

      return renderPage(header, body)

    except Exception as e:
      traceback.print_exc()
      return Response("Internal Server Error\n" + str(e), status=500)
