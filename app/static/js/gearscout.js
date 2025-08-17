// gear_scout.js — ES module (icon-bound source loads; per-source cache; reveal-after-populate)

// ---------- tiny utils ----------
const onReady = (fn) =>
  (document.readyState === "loading"
    ? document.addEventListener("DOMContentLoaded", fn, { once: true })
    : fn());

async function fetchHTML(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}

function revealDetails(li) {
  const details = li.querySelector(".result-details");
  if (!details) return;
  li.classList.add("expanded", "open");
  li.setAttribute("aria-expanded", "true");
  details.hidden = false;
  details.style.display = "block";
}

function hideDetails(li) {
  const details = li.querySelector(".result-details");
  if (!details) return;
  li.classList.remove("expanded", "open");
  li.setAttribute("aria-expanded", "false");
  details.style.display = "none";
  details.hidden = true;
}

// ---------- cache: per itemId -> { sourceKey: html } ----------
const ROW_CACHE = new Map();
const VALID_SOURCES = new Set(["drops", "merchants", "recipes"]);

function endpointFor(itemId, source) {
  // /api/render/item/<id>/<source>
  return `/api/render/item/${encodeURIComponent(itemId)}/${encodeURIComponent(source)}`;
}

function setActiveIcon(container, source) {
  try {
    const icons = container.querySelectorAll("[data-source]");
    icons.forEach((el) => {
      el.classList.toggle("active", String(el.dataset.source).toLowerCase() === source);
      el.setAttribute("aria-pressed", String(String(el.dataset.source).toLowerCase() === source));
    });
  } catch (_) {}
}

function initGearScout() {
  const resultsRoot = document.getElementById("gearscout-results");
  if (!resultsRoot) return;

  // 1) Header toggle (no fetching)
  resultsRoot.addEventListener("click", (ev) => {
    const header = ev.target.closest(".result-item .result-header");
    if (!header || !resultsRoot.contains(header)) return;

    // If the actual click was on a data-source icon, let the other handler do the work.
    if (ev.target.closest("[data-source]")) return;

    const li = header.closest(".result-item");
    const details = li?.querySelector(".result-details");
    if (!li || !details) return;

    const isClosed = !(li.classList.contains("expanded") || li.classList.contains("open"));
    if (isClosed) revealDetails(li);
    else {
      details.innerHTML = "";
      hideDetails(li);
    }
  });

  // 2) Source-icon click → load that section only
  resultsRoot.addEventListener("click", async (ev) => {
    const icon = ev.target.closest("[data-source]");
    if (!icon || !resultsRoot.contains(icon)) return;

    const li = icon.closest(".result-item");
    const id = li?.dataset?.itemid;
    const details = li?.querySelector(".result-details");
    if (!li || !id || !details) return;

    const source = String(icon.dataset.source || "").toLowerCase();
    if (!VALID_SOURCES.has(source)) return;

    // Ensure details region is visible
    if (!(li.classList.contains("expanded") || li.classList.contains("open"))) {
      revealDetails(li);
    }

    // Activate icon state
    setActiveIcon(li, source);

    // Fetch or use cache
    const perItem = ROW_CACHE.get(id) || {};
    if (perItem[source]) {
      details.innerHTML = perItem[source];
      return;
    }

    details.innerHTML = `<div class="muted">Loading ${source}…</div>`;
    try {
      const html = await fetchHTML(endpointFor(id, source));
      perItem[source] = html;
      ROW_CACHE.set(id, perItem);
      details.innerHTML = html;
    } catch (e) {
      console.error(e);
      details.innerHTML = `<div class="error">Failed to load ${source}.</div>`;
    }
  });

  // 3) Keyboard: Enter/Space on a [data-source] icon triggers the same action as click
  resultsRoot.addEventListener("keydown", (ev) => {
    const el = ev.target.closest("[data-source]");
    if (!el || !resultsRoot.contains(el)) return;
    if (ev.key === "Enter" || ev.key === " ") {
      ev.preventDefault();
      el.click();
    }
  });
}

onReady(initGearScout);

// ---------- exports ----------
export { initGearScout };
export default { initGearScout };
