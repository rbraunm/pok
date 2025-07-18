NAME = "Exports"

from pathlib import Path
URL_PREFIX = "/" + Path(__file__).stem

from flask import Response
from app import renderPage, PoKJSONEncoder
import json

from api.models.exports import get_sample
from api.models.schema import list_tables, describe_table

def register(app):
  @app.route(URL_PREFIX)
  def exportsHome():
    dataTables = list_tables()
    schemaTables = list_tables()
    header = f'''
<div class="headerRow">
  <div class="headerLeft">
    <h1>{NAME}</h1>
    <input type="text" id="activeFilter" class="filter-box" placeholder="Search data tables..." onkeyup="filterCurrent(this.value)">
  </div>
  <div class="headerRight">
    <button class="download-btn" onclick="downloadCurrent()">Download JSON</button>
    <div class="export-tabs">
      <button class="tab-btn active" onclick="showTab('data')">Data</button>
      <button class="tab-btn" onclick="showTab('schema')">Schema</button>
    </div>
  </div>
</div>'''

    def makeListBlock(typeName, tables):
      return "".join(
        f'''
<li onclick="toggleData('{typeName}', '{t}', this, event)">
  <div class="row-header">
    <span class="row-label">{t}</span>
    <button class="inline-download hidden" onclick="downloadSingle(event, '{typeName}', '{t}')">Download JSON</button>
  </div>
  <div class="data-container">
    <pre class="data-viewer"></pre>
  </div>
</li>''' for t in tables
      )

    dataLinks = makeListBlock("data", dataTables)
    schemaLinks = makeListBlock("schema", schemaTables)

    body = f'''
<div id="data" class="tab-section active">
  <ul class="export-list" id="data-list">{dataLinks}</ul>
</div>
<div id="schema" class="tab-section">
  <ul class="export-list" id="schema-list">{schemaLinks}</ul>
</div>

<script>
function downloadCurrent() {{
  const tab = document.querySelector('.tab-btn.active')?.textContent.toLowerCase();
  if (!tab) return;
  downloadAll(tab);
}}

function showTab(tabName) {{
  const currentExpanded = document.querySelector('li.expanded .row-label');
  const expandedTable = currentExpanded ? currentExpanded.textContent.trim() : null;

  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-section').forEach(sec => sec.classList.remove('active'));
  document.querySelector(`.tab-btn[onclick="showTab('${{tabName}}')"]`).classList.add('active');
  document.getElementById(tabName).classList.add('active');
  document.getElementById("activeFilter").placeholder = "Search " + tabName + " tables...";
  filterCurrent(document.getElementById("activeFilter").value);

  if (!expandedTable) return;

  const labels = document.querySelectorAll(`#${{tabName}}-list li .row-label`);
  labels.forEach(label => {{
    if (label.textContent.trim() === expandedTable) {{
      const li = label.closest('li');
      li.classList.add('expanded');

      const pre = li.querySelector('pre.data-viewer');
      const btn = li.querySelector('button.inline-download');

      pre.textContent = "Loading...";
      btn.classList.remove('hidden');
      btn.setAttribute("onclick", `downloadSingle(event, '${{tabName}}', '${{expandedTable}}')`);

      fetch("{URL_PREFIX}/" + tabName + "/" + expandedTable + "/raw")
        .then(r => r.text())
        .then(txt => {{
          pre.textContent = txt;
          requestAnimationFrame(() => {{
            li.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
          }});
        }})
        .catch(err => pre.textContent = "Error loading data.");
    }}
  }});
}}

function getCurrentListId() {{
  return document.querySelector('.tab-section.active ul')?.id;
}}

function filterCurrent(term) {{
  const listId = getCurrentListId();
  if (!listId) return;
  document.querySelectorAll('#' + listId + ' li').forEach(li => {{
    const labelEl = li.querySelector('.row-label');
    const text = labelEl ? labelEl.textContent.toLowerCase() : '';
    li.style.display = text.includes(term.toLowerCase()) ? '' : 'none';
  }});
}}

function toggleData(type, table, liEl, event) {{
  if (event.target.closest('pre.data-viewer')) {{
    return; // don't toggle when clicking inside the JSON view
  }}

  const container = liEl.querySelector('.data-container');
  const pre = container.querySelector('pre.data-viewer');
  const btn = liEl.querySelector('button.inline-download');
  const expanded = liEl.classList.contains('expanded');

  if (expanded) {{
    liEl.classList.remove('expanded');
    pre.textContent = '';
    btn.classList.add('hidden');
    return;
  }}

  document.querySelectorAll('.export-list li.expanded').forEach(other => {{
    other.classList.remove('expanded');
    other.querySelector('pre.data-viewer').textContent = '';
    other.querySelector('button.inline-download').classList.add('hidden');
  }});

  liEl.classList.add('expanded');
  pre.textContent = 'Loading...';
  btn.classList.remove('hidden');
  btn.setAttribute("onclick", `downloadSingle(event, '${{type}}', '${{table}}')`);
  fetch("{URL_PREFIX}/" + type + "/" + table + "/raw")
    .then(r => r.text())
    .then(txt => pre.textContent = txt)
    .catch(err => pre.textContent = "Error loading data.");
}}

function downloadAll(type) {{
  const path = type === 'data' ? '{URL_PREFIX}/data/raw' : '{URL_PREFIX}/schema/raw';
  const file = type === 'data' ? 'pok-data-all.json' : 'pok-schema-all.json';
  fetch(path).then(r => r.text()).then(txt => {{
    const blob = new Blob([txt], {{type:'application/json'}});
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), {{
      href:url, download:file
    }});
    document.body.appendChild(a); a.click(); a.remove();
  }});
}}

function downloadSingle(event, type, table) {{
  event.stopPropagation();
  const url = "{URL_PREFIX}/" + type + "/" + table + "/raw";
  fetch(url).then(r => r.text()).then(txt => {{
    const blob = new Blob([txt], {{type:'application/json'}});
    const link = Object.assign(document.createElement('a'), {{
      href: URL.createObjectURL(blob),
      download: table + '.json'
    }});
    document.body.appendChild(link); link.click(); link.remove();
  }});
}}
</script>
'''
    return renderPage(header, body)

  @app.route(f"{URL_PREFIX}/data/<table>/raw")
  def exportDataRaw(table):
    return Response(json.dumps(get_sample(table), cls=PoKJSONEncoder, indent=2), mimetype="application/json")

  @app.route(f"{URL_PREFIX}/data/raw")
  def exportAllData():
    tableList = list_tables()
    allTables = {tbl: get_sample(tbl) for tbl in tableList}
    return Response(json.dumps(allTables, cls=PoKJSONEncoder, indent=2), mimetype="application/json")

  @app.route(f"{URL_PREFIX}/schema/<table>/raw")
  def exportSchemaRaw(table):
    return Response(json.dumps(describe_table(table), cls=PoKJSONEncoder, indent=2), mimetype="application/json")

  @app.route(f"{URL_PREFIX}/schema/raw")
  def exportAllSchema():
    tableList = list_tables()
    allSchemas = {tbl: describe_table(tbl) for tbl in tableList}
    return Response(json.dumps(allSchemas, cls=PoKJSONEncoder, indent=2), mimetype="application/json")
