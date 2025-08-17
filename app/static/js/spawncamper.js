const onReady = (fn) => {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn, { once:true });
  else fn();
};

onReady(() => {
  const cardsRoot = document.getElementById('sc-cards');
  const addBtn = document.getElementById('sc-add');
  if (!addBtn || !cardsRoot) { console.error('SpawnCamper: root elements missing'); return; }

  const requestNotifyPermission = () => { try { if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission(); } catch (e) {} };
  const notify = (title, body) => { try { if ('Notification' in window && Notification.permission === 'granted') new Notification(title, { body }); } catch (e) {} };

  const playBeep = (durMs = 220) => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator(), gain = ctx.createGain();
      osc.type='sine'; osc.frequency.value=880; gain.gain.value=0.02;
      osc.connect(gain); gain.connect(ctx.destination); osc.start();
      setTimeout(()=>{ osc.stop(); ctx.close(); }, durMs);
    } catch(e){}
  };

  function parseDuration(input){
    if (!input) return 0;
    input = String(input).trim().toLowerCase();
    if (/^\d{1,2}:\d{2}(:\d{2})?$/.test(input)) {
      const p = input.split(':').map(Number); let h=0,m=0,s=0;
      if (p.length===3) [h,m,s]=p; if (p.length===2) [m,s]=p;
      return h*3600 + m*60 + s;
    }
    let total = 0, re = /(\d+(?:\.\d+)?)(h|m|s)/g, m;
    while ((m = re.exec(input)) !== null) {
      const val = parseFloat(m[1]), u = m[2];
      if (u==='h') total += val*3600; if (u==='m') total += val*60; if (u==='s') total += val;
    }
    if (total > 0) return Math.round(total);
    if (/^\d+(?:\.\d+)?$/.test(input)) return Math.round(parseFloat(input));
    return 0;
  }

  const fmt = (t) => {
    t = Math.max(0, Math.floor(t));
    const h = Math.floor(t/3600), m = Math.floor((t%3600)/60), s = t%60;
    return h ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
             : `${m}:${String(s).padStart(2,'0')}`;
  };

  let nextId = 1;
  const cards = new Map();

  function setIconState(btn, enabled, onTitle, offTitle, onEmoji, offEmoji) {
    btn.classList.toggle('off', !enabled);
    btn.setAttribute('aria-pressed', enabled ? 'true' : 'false');
    btn.title = enabled ? onTitle : offTitle;
    if (onEmoji && offEmoji) btn.textContent = enabled ? onEmoji : offEmoji;
  }

  // ==== URL-safe Base64 helpers (UTF-8) ====
  const b64url = {
    enc(str){
      const bytes = new TextEncoder().encode(str);
      let bin = '';
      for (let i=0;i<bytes.length;i++) bin += String.fromCharCode(bytes[i]);
      return btoa(bin).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
    },
    dec(s){
      let base = s.replace(/-/g,'+').replace(/_/g,'/');
      while (base.length % 4) base += '=';
      const bin = atob(base);
      const bytes = new Uint8Array(bin.length);
      for (let i=0;i<bin.length;i++) bytes[i] = bin.charCodeAt(i);
      return new TextDecoder().decode(bytes);
    }
  };

  // ==== URL persistence (debounced single-writer) ====
  // Schema: {v:2, t:[{n, b, x, s, N}]}
  // n=name, b=baseSec, x=baseText, s=beep(0/1), N=notify(0/1)
  function serializeAll() {
    const data = { v:2, t:[] };
    const children = Array.from(cardsRoot.children);
    for (const el of children) {
      const id = el.__card_id;
      const c = id ? cards.get(id) : null;
      if (!c) continue;
      data.t.push({
        n: c.name || 'Spawn',
        b: Math.max(0, c.base|0),
        x: c.baseText || fmt(c.base),
        s: c.beep ? 1 : 0,
        N: c.notify ? 1 : 0
      });
    }
    return data;
  }

  function saveToURLNow() {
    try {
      const data = serializeAll();
      const url = new URL(location.href);
      if (data.t.length > 0) {
        const json = JSON.stringify(data);
        url.searchParams.set('sc', b64url.enc(json));
      } else {
        url.searchParams.delete('sc');
      }
      history.replaceState(null, '', url);
    } catch (e) {
      console.warn('SpawnCamper: failed to save timers to URL', e);
    }
  }

  let loadingFromURL = false;
  let saveDebounce = 0;
  function scheduleSave() {
    if (loadingFromURL) return;
    if (saveDebounce) clearTimeout(saveDebounce);
    saveDebounce = setTimeout(() => { saveDebounce = 0; saveToURLNow(); }, 120);
  }

  function loadFromURL() {
    const sp = new URLSearchParams(location.search);
    const raw = sp.get('sc');
    if (!raw) return;
    let data;
    try {
      const jsonStr = b64url.dec(raw);
      data = JSON.parse(jsonStr);
    } catch (e) {
      console.warn('SpawnCamper: invalid ?sc= payload', e);
      return;
    }
    if (!data || data.v !== 2 || !Array.isArray(data.t)) return;

    loadingFromURL = true;
    try {
      for (const t of data.t) {
        const name = typeof t.n === 'string' ? t.n : 'Spawn';
        const base = Number.isFinite(t.b) && t.b > 0 ? Math.floor(t.b) : parseDuration(t.x || '');
        if (base <= 0) continue;
        const baseText = typeof t.x === 'string' && t.x.trim() ? t.x : fmt(base);
        const beep = !!t.s;
        const notify = !!t.N;
        const timer = new SpawnTimer(name, base, baseText, beep, notify);
        const el = makeCardEl(timer);
        cards.set(timer.id, timer);
        cardsRoot.append(el);
      }
    } finally {
      loadingFromURL = false;
    }
  }

  // Inline editor with width clamp
  function inlineEdit(textEl, initialValue, opts) {
    const { onCommit, validate, placeholder="", minWidth=100, maxWidth=200 } = opts || {};
    const input = document.createElement('input');
    input.type = 'text';
    input.value = initialValue;
    input.placeholder = placeholder;
    input.className = 'sc-inline-input';
    const w = Math.max(minWidth, Math.min(maxWidth, textEl.getBoundingClientRect().width + 20));
    input.style.minWidth = Math.round(w) + 'px';
    input.style.maxWidth = Math.round(maxWidth) + 'px';

    const parent = textEl.parentNode;
    parent.replaceChild(input, textEl);
    input.focus();
    input.select();

    function finish(commit) {
      const val = input.value.trim();
      const ok = commit ? (validate ? validate(val) : true) : false;
      if (commit && ok) { onCommit && onCommit(val); scheduleSave(); }
      parent.replaceChild(textEl, input);
    }

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); finish(true); }
      if (e.key === 'Escape') { e.preventDefault(); finish(false); }
    });
    input.addEventListener('blur', () => finish(true));
  }

  function makeCardEl(card) {
    const el = document.createElement('div');
    el.className = 'sc-card';
    el.innerHTML = `
      <div class="sc-card-header">
        <h3 class="sc-name" tabindex="0" title="Click to rename" aria-label="Rename (click)"></h3>
        <div class="sc-icons">
          <button class="sc-icon sc-danger" data-act="delete" title="Delete timer" aria-label="Delete timer">❌</button>
        </div>
      </div>

      <div class="sc-times">
        <div class="sc-times-left">
          <span class="sc-rem" data-k="remain"></span>
          <span class="sc-sep">/</span>
          <span class="sc-base" data-k="base" tabindex="0" title="Click to edit base">00:00</span>
        </div>
        <div class="sc-times-ctrl">
          <button class="sc-icon" data-act="reset" title="Reset timer" aria-label="Reset timer">🔄</button>
          <button class="sc-icon" data-act="toggle-beep" aria-label="Toggle sound" title="Sound: On">🔊</button>
          <button class="sc-icon" data-act="toggle-notify" aria-label="Toggle notifications" title="Notify: On">🔔</button>
        </div>
      </div>
    `;
    el.__card_id = card.id;

    const qs = (sel) => el.querySelector(sel);
    const setText = (k, v) => qs('[data-k="'+k+'"]').textContent = v;

    const nameEl = qs('.sc-name');
    nameEl.textContent = card.name || 'Spawn';
    setText('base', fmt(card.base));
    setText('remain', fmt(card.remaining()));

    const beepBtn  = qs('[data-act="toggle-beep"]');
    const notifBtn = qs('[data-act="toggle-notify"]');
    setIconState(beepBtn,  card.beep,   "Sound: On",  "Sound: Off", "🔊", "🔇");
    setIconState(notifBtn, card.notify, "Notify: On", "Notify: Off", "🔔", "🔕");

    // Start/Pause (state not persisted)
    const remEl = qs('[data-k="remain"]');
    remEl.setAttribute('role', 'button');
    remEl.setAttribute('tabindex', '0');

    const setRunVisual = () => {
      const running = card.running === true;
      remEl.title = running ? 'Pause timer' : 'Start timer';
      remEl.setAttribute('aria-label', remEl.title);
      remEl.setAttribute('aria-pressed', running ? 'true' : 'false');
      remEl.classList.toggle('sc-running', running);
      remEl.classList.toggle('sc-paused', !running);
    };
    card._setRunVisual = setRunVisual;
    setRunVisual();

    const toggleRun = () => { if (card.running) card.pause(); else card.start(); };
    remEl.addEventListener('click', (e) => { e.preventDefault(); toggleRun(); });
    remEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') { e.preventDefault(); toggleRun(); }
    });

    // Rename
    const beginNameEdit = () => inlineEdit(nameEl, card.name, {
      onCommit: (val) => { card.name = val || 'Spawn'; nameEl.textContent = card.name; },
      validate: () => true,
      minWidth: 80, maxWidth: 180
    });
    nameEl.addEventListener('click', beginNameEdit);
    nameEl.addEventListener('keydown', (e)=>{ if (e.key === 'Enter') { e.preventDefault(); beginNameEdit(); } });

    // Edit Base
    const baseEl = qs('[data-k="base"]');
    const beginBaseEdit = () => inlineEdit(baseEl, card.baseText, {
      onCommit: (val) => {
        const sec = parseDuration(val);
        if (sec > 0) { card.setBase(sec, val); baseEl.textContent = fmt(card.base); }
        else { alert('Enter a valid duration (e.g., 22m, 1h30m, 200s, 00:22:00).'); }
      },
      validate: (val) => parseDuration(val) > 0,
      minWidth: 120, maxWidth: 200
    });
    baseEl.addEventListener('click', beginBaseEdit);
    baseEl.addEventListener('keydown', (e)=>{ if (e.key === 'Enter') { e.preventDefault(); beginBaseEdit(); } });

    // Card actions
    el.addEventListener('click', (e) => {
      const btn = e.target.closest('button'); if (!btn) return;
      const act = btn.getAttribute('data-act');

      if (act === 'toggle-beep') {
        card.beep = !card.beep;
        setIconState(beepBtn, card.beep, "Sound: On", "Sound: Off", "🔊", "🔇");
        scheduleSave();
        return;
      }
      if (act === 'toggle-notify') {
        card.notify = !card.notify;
        if (card.notify) { try { Notification && requestNotifyPermission(); } catch(e){} }
        setIconState(notifBtn, card.notify, "Notify: On", "Notify: Off", "🔔", "🔕");
        scheduleSave();
        return;
      }
      if (act === 'reset') { card.reset(); return; } // not persisted
      if (act === 'delete') { cards.delete(card.id); el.remove(); scheduleSave(); return; }
    });

    card._render = () => { setText('remain', fmt(card.remaining())); };
    return el;
  }

  class SpawnTimer {
    constructor(name, base, baseText, beep=true, notify=true) {
      this.id = nextId++;
      this.name = name || 'Spawn';
      this.base = base;
      this.baseText = baseText;
      this.beep = !!beep;
      this.notify = !!notify;
      this.running = false;
      this._interval = null;
      this._endAt = null;
      this._remaining = null;
      this._warned = false;
      this._setRunVisual = null;
      this._render = null;
    }
    remaining() {
      if (this.running && this._endAt) return Math.max(0, Math.round((this._endAt - Date.now())/1000));
      if (!this.running && this._remaining != null) return Math.max(0, this._remaining);
      return this.base;
    }
    setBase(sec, text) {
      this.base = sec; this.baseText = text;
      if (!this.running) { this._endAt = null; this._remaining = null; }
      this._warned = false;
      if (this._render) this._render();
      scheduleSave();
    }
    start() {
      requestNotifyPermission();
      const dur = this._remaining != null ? this._remaining : this.remaining();
      this._endAt = Date.now() + dur*1000;
      this._remaining = null;
      this.running = true;
      this._warned = false;
      if (this._interval) clearInterval(this._interval);
      this._interval = setInterval(() => this._tick(), 250);
      if (this._setRunVisual) this._setRunVisual();
    }
    pause() {
      if (this._endAt) this._remaining = Math.max(0, Math.round((this._endAt - Date.now())/1000));
      this.running = false;
      if (this._interval) clearInterval(this._interval);
      this._interval = null;
      if (this._setRunVisual) this._setRunVisual();
    }
    reset() {
      this.running = false; this._endAt = null; this._remaining = null; this._warned = false;
      if (this._interval) clearInterval(this._interval);
      this._interval = null;
      if (this._setRunVisual) this._setRunVisual();
      if (this._render) this._render();
    }
    _tick() {
      const rem = this.remaining();
      if (rem <= 60 && rem > 0 && !this._warned) {
        this._warned = true;
        if (this.notify) notify(this.name + " in 1 minute", "Get into position.");
        if (this.beep) playBeep(300);
      }
      if (rem <= 0) {
        this.running = false;
        if (this._interval) clearInterval(this._interval);
        this._interval = null;
        if (this.notify) notify(this.name + " up!", "Timer complete.");
        if (this.beep) { playBeep(500); setTimeout(()=>playBeep(500), 200); }
        if (this._setRunVisual) this._setRunVisual();
      }
      if (this._render) this._render();
    }
  }

  // Add timer
  addBtn.addEventListener('click', (e) => {
    try {
      e.preventDefault();
      const name   = document.getElementById('sc-name').value.trim() || 'Spawn';
      const durTxt = document.getElementById('sc-duration').value.trim() || '20m';
      const beep   = document.getElementById('sc-sound').checked;
      const notify = !!document.getElementById('sc-notify').checked;
      const dur = parseDuration(durTxt);
      if (dur <= 0) { alert('Please enter a valid duration (e.g., 22m, 1h30m, 200s, 00:22:00).'); return; }
      const timer = new SpawnTimer(name, dur, durTxt, beep, notify);
      const el = makeCardEl(timer);
      cards.set(timer.id, timer);
      cardsRoot.prepend(el);
      scheduleSave();
    } catch (err) {
      console.error('SpawnCamper add failed:', err);
      alert('Could not add spawn timer (see console).');
    }
  });

  // Initial load from URL
  loadFromURL();

  // Keep view in sync on back/forward
  window.addEventListener('popstate', () => {
    loadingFromURL = true;
    cards.clear();
    while (cardsRoot.firstChild) cardsRoot.removeChild(cardsRoot.firstChild);
    nextId = 1;
    loadingFromURL = false;
    loadFromURL();
  });
});
