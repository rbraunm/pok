/* =======================================================================
 * everquest_tooltip.js — Full-featured version w/ auto-binding
 * -----------------------------------------------------------------------
 * Visual spec:
 *  • CSS-only gold bevel with top/left highlight, bottom/right shadow
 *  • Background: /static/img/everquest_tooltip_background.png
 *  • Midnight-blue tint: rgba(4,16,40,0.85)
 * Features:
 *  • Auto-binds to all .eqtooltip[data-type][data-id] on DOMContentLoaded
 *  • Public API: EQTooltip.init(), showTooltip(type, id, event), hideTooltip()
 * =======================================================================
 */
const SLOT_BITMASKS = {
  7:  [1 << 2,  "Head"],
  8:  [1 << 17, "Chest"],
  9:  [1 << 7,  "Arms"],
  10: [1 << 9,  "Wrist"],
  11: [1 << 12, "Hands"],
  12: [1 << 18, "Legs"],
  13: [1 << 19, "Feet"],
  14: [1 << 8,  "Back"],
  30: [1 << 21, "Primary"],
  31: [1 << 22, "Secondary"],
  3:  [1 << 1,  "Ear"],
  4:  [1 << 15, "Finger"],
  5:  [1 << 5,  "Neck"],
  2:  [1 << 11, "Range"]
};

function decodeSlots(slotBitmask) {
  if (!slotBitmask || slotBitmask === 0) return '';

  const allSlotMask = Object.values(SLOT_BITMASKS)
    .reduce((sum, [mask]) => sum | mask, 0);

  if ((slotBitmask & allSlotMask) === allSlotMask) return 'Any';

  return Object.values(SLOT_BITMASKS)
    .filter(([mask]) => (slotBitmask & mask) !== 0)
    .map(([, name]) => name)
    .join(', ');
}

const CLASS_BITMASK = {
  "WAR": 1 << 0,
  "CLR": 1 << 1,
  "PAL": 1 << 2,
  "RNG": 1 << 3,
  "SHD": 1 << 4,
  "DRU": 1 << 5,
  "MNK": 1 << 6,
  "BRD": 1 << 7,
  "ROG": 1 << 8,
  "SHM": 1 << 9,
  "NEC": 1 << 10,
  "WIZ": 1 << 11,
  "MAG": 1 << 12,
  "ENC": 1 << 13,
  "BST": 1 << 14,
  "BER": 1 << 15
};

function decodeClasses(classBitmask) {
  const allClassMask = Object.values(CLASS_BITMASK).reduce((sum, mask) => sum | mask, 0);
  if ((classBitmask & allClassMask) === allClassMask) return 'Any';

  return Object.entries(CLASS_BITMASK)
    .filter(([_, mask]) => (classBitmask & mask) !== 0)
    .map(([name]) => name)
    .join(' ') || 'None';
}

const RACE_BITMASK = {
  "HUM": 1 << 0,  // Human
  "BAR": 1 << 1,  // Barbarian
  "ERU": 1 << 2,  // Erudite
  "WEL": 1 << 3,  // Wood Elf
  "HIE": 1 << 4,  // High Elf
  "DEF": 1 << 5,  // Dark Elf
  "HEF": 1 << 6,  // Half Elf
  "DWF": 1 << 7,  // Dwarf
  "TRL": 1 << 8,  // Troll
  "OGR": 1 << 9,  // Ogre 
  "HFL": 1 << 10, // Halfling
  "GNM": 1 << 11, // Gnome
  "IKS": 1 << 12, // Iksar
  "VAH": 1 << 13, // Vah Shir
  "FRG": 1 << 14  // Froglok
};


function decodeRaces(raceBitmask) {
  const allRaceMask = Object.values(RACE_BITMASK).reduce((sum, mask) => sum | mask, 0);
  if ((raceBitmask & allRaceMask) === allRaceMask) return 'Any';

  return Object.entries(RACE_BITMASK)
    .filter(([_, mask]) => (raceBitmask & mask) !== 0)
    .map(([name]) => name)
    .join(' ') || 'None';
}

(function injectTooltipStyles() {
  if (document.getElementById('eqtooltip-style')) return;

  const css = `
  .eqtooltip-container {
    all: initial; /* reset all inherited styles */

    /* Background: parchment texture with midnight blue tint */
    background:
      linear-gradient(rgba(4,16,40,0.85), rgba(4,16,40,0.85)),
      url('/static/img/everquest_tooltip_background.png') repeat;
    background-blend-mode: multiply !important;
    background-size: cover !important;
    background-position: center !important;

    /* Golden border */
    border: 2px solid transparent !important;
    border-radius: 4px !important;
    background-origin: border-box;
    background-clip: padding-box, border-box;

    border-image: linear-gradient(
      135deg,
      #f9e49a,     /* light gold */
      #d7b95d,
      #b68d27,     /* deeper gold */
      #d7b95d,
      #f9e49a
    ) 1 stretch !important;

    /* Inner bevel and outer glow */
    box-shadow:
      inset 0 0 0 1px rgba(0,0,0,0.85),
      0 0 4px rgba(0,0,0,0.6) !important;

    max-width: 350px !important;
    padding: 6px 8px !important;
    color: #EAEAEA !important;
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 12px !important;
    line-height: 1.25 !important;
    text-shadow: 1px 1px 0 #000 !important;
    text-align: left !important;
    letter-spacing: normal !important;
    word-spacing: normal !important;
    vertical-align: baseline !important;
    text-indent: 0 !important;
    white-space: normal !important;

    position: absolute !important;
    pointer-events: none;
    z-index: 10000 !important;
    opacity: 0;
  }
  
  .eqtooltip-container .name         { font-size: 18px !important; font-weight: 700 !important; margin-bottom: 2px !important; }
  .eqtooltip-container .flags        { color: #E0DFDB !important; }
  .eqtooltip-container .section      { display: block !important; margin: 2px 0 !important; line-height: 1.4 !important; }
  .eqtooltip-container .label        { font-weight: 700 !important; }
  .eqtooltip-container .stat-heroic  { color: #6cf !important; }
  .eqtooltip-container .effect       { color: #FFDF00 !important; }
  `;
  
  const style = document.createElement('style');
  style.id = 'eqtooltip-style';
  style.textContent = css;
  document.head.appendChild(style);
})();

const EQTooltip = (() => {
  const cache = new Map();
  let tooltipEl = null;
  let config = {
    selector: '.eqtooltip',
    delay: 150
  };

  function ensureTooltipEl() {
    if (tooltipEl) return;
    tooltipEl = document.createElement('div');
    tooltipEl.className = 'eqtooltip-container';
    document.body.appendChild(tooltipEl);
  }

  function has(v) {
    return v !== undefined && v !== null && v !== '' && v !== 0 && v !== '0';
  }

  function renderItem(D) {
    const out = [], push = h => out.push(h);
  
    push(`<div class="name">${D.Name}</div>`);
    if (has(D.flags)) push(`<div class="flags">${D.flags}</div>`);
  
    if (has(D.slots)) {
      const slotText = decodeSlots(parseInt(D.slots, 10));
      if (slotText) push(`<div class="section"><span class="label">Slot:</span> ${slotText}</div>`);
    }
  
    if (has(D.skill) || has(D.delay)) {
      const parts = [];
      if (has(D.skill)) parts.push(`Skill: ${D.skill}`);
      if (has(D.delay)) parts.push(`Atk Delay: ${D.delay}`);
      push(`<div class="section">${parts.join(' ')}</div>`);
    }
  
    if (has(D.damage) || has(D.dmgBonus) || has(D.ac)) {
      const parts = [];
      if (has(D.damage)) parts.push(`DMG: ${D.damage}`);
      if (has(D.dmgBonus)) parts.push(`Dmg Bonus: ${D.dmgBonus}`);
      if (has(D.ac)) parts.push(`AC: ${D.ac}`);
      push(`<div class="section">${parts.join(' ')}</div>`);
    }
  
    if (has(D.placeable)) push(`<div class="section">${D.placeable}</div>`);
  
    // Primary + Heroic Stats
    const stats = ['str', 'dex', 'sta', 'cha', 'wis', 'int', 'agi', 'hp', 'mana', 'endur'];
    const statParts = [];
    stats.forEach(stat => {
      const cap = stat.toUpperCase();
      const baseVal = D[stat];
      const base = has(baseVal) 
        ? (baseVal > 0 ? `+${baseVal}` : `${baseVal}`) 
        : '';

      const heroVal = D[`hero${cap}`];
      const hero = (has(heroVal) && heroVal > 0) 
        ? `<span class="stat-heroic">+${heroVal}</span>` 
        : '';

      if (base || hero) {
        statParts.push(`${cap}: ${base}${base && hero ? ' ' : ''}${hero}`);
      }
    });
    if (statParts.length) push(`<div class="section">${statParts.join(' ')}</div>`);
  
    // Resists
    const resists = { fr: 'SV FIRE', dr: 'SV DISEASE', cr: 'SV COLD', mr: 'SV MAGIC', pr: 'SV POISON' };
    const resistParts = [];
    Object.entries(resists).forEach(([key, label]) => {
      if (has(D[key])) resistParts.push(`${label}: +${D[key]}`);
    });
    if (resistParts.length) push(`<div class="section">${resistParts.join(' ')}</div>`);
  
    // Attack, Regen, Misc
    const misc = [];
    if (has(D.attack)) misc.push(`Attack: +${D.attack}`);
    if (has(D.hpregen)) misc.push(`HP Regen: +${D.hpregen}`);
    if (has(D.manaregen)) misc.push(`Mana Regeneration: +${D.manaregen}`);
    if (has(D.clairvoyance)) misc.push(`Clairvoyance: +${D.clairvoyance}`);
    if (has(D.spelldamage)) misc.push(`Spell Damage: +${D.spelldamage}`);
    if (has(D.healamt)) misc.push(`Heal Amount: +${D.healamt}`);
    if (misc.length) push(`<div class="section">${misc.join(' ')}</div>`);
  
    if (has(D.reqlevel)) push(`<div class="section">Required level of ${D.reqlevel}.</div>`);
    if (has(D.reclevel)) push(`<div class="section">Recommended level ${D.reclevel}.</div>`);
  
    if (has(D.effect)) push(`<div class="section"><span class="label">Effect:</span> <span class="effect">${D.effect}</span></div>`);
    if (has(D.focuseffect) && D.focuseffect !== -1) {
      push(`<div class="section"><span class="label">Focus:</span> ${D.focuseffect}</span></div>`);
    }
  
    // WT, Size
    if (has(D.weight) || has(D.size)) {
      push(`<div class="section">WT: ${D.weight || 0} Size: ${D.size || 'Unknown'}</div>`);
    }
  
    // Class / Race
    if (has(D.classes)) push(`<div class="section"><span class="label">Class:</span> ${decodeClasses(parseInt(D.classes, 10))}</div>`);
    if (has(D.races)) push(`<div class="section"><span class="label">Race:</span> ${decodeRaces(parseInt(D.races, 10))}</div>`);
  
    // Augmentation Slots / Slot Info
    if (has(D.slotinfo)) push(`<div class="section">${D.slotinfo}</div>`);
  
    return out.join('');
  }

  function renderSpell(S) {
    const push = (arr, h) => { if (h) arr.push(h); };
    const out = [];
  
    push(out, `<div class="name">Spell: ${S.name}</div>`);
    if (has(S.spelllevel)) push(out, `<div class="section">Level: ${S.spelllevel}</div>`);
    if (has(S.skill))      push(out, `<div class="section">Skill: ${S.skill}</div>`);
  
    if (has(S.mana)) {
      let manaText = `Mana: ${S.mana}`;
      if (has(S.mana_min) && has(S.mana_max)) {
        manaText += ` (${S.mana_min} - ${S.mana_max})`;
      }
      push(out, `<div class="section">${manaText}</div>`);
    }
  
    if (has(S.casttime)) {
      const sec = parseFloat(S.casttime).toFixed(1);
      push(out, `<div class="section">Cast: ${sec} sec</div>`);
    }
  
    if (has(S.recasttime)) push(out, `<div class="section">Recast: ${S.recasttime} sec</div>`);
    if (has(S.recovery_time)) push(out, `<div class="section">Recovery: ${S.recovery_time} sec</div>`);
    if (has(S.caster)) push(out, `<div class="section">Caster: ${S.caster}</div>`);
  
    if (has(S.targettype)) push(out, `<div class="section">Target: ${S.targettype}</div>`);
    if (has(S.range)) {
      let rangeStr = `Range: ${S.range}`;
      if (has(S.aoerange)) rangeStr += ` (AE: ${S.aoerange})`;
      push(out, `<div class="section">${rangeStr}</div>`);
    }
  
    if (has(S.buffduration)) {
      const durationSec = parseInt(S.buffduration);
      const durationHMS = formatSecondsToHMS(durationSec);
      push(out, `<div class="section">Duration: ${durationHMS}</div>`);
    }
  
    if (has(S.description)) push(out, `<div class="section">${S.description}</div>`);
  
    if (has(S.you_cast)) push(out, `<div class="section">On You: ${S.you_cast}</div>`);
    if (has(S.cast_on_other)) push(out, `<div class="section">On Other: ${S.cast_on_other}</div>`);
    if (has(S.spell_fades)) push(out, `<div class="section">Wears Off: ${S.spell_fades}</div>`);
  
    return out.join('');
  }
  
  function formatSecondsToHMS(totalSeconds) {
    if (!totalSeconds || totalSeconds === 0) return 'Instant';
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    let result = '';
    if (hours) result += `${hours}:`;
    result += `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    return result;
  }

  function renderNpc(N) {
    const out = [], push = h => out.push(h);
  
    // Name + Lastname
    const fullName = N.lastname ? `${N.name} ${N.lastname}` : N.name;
    push(out, `<div class="name">${fullName}</div>`);
  
    // Level / Race / Class / Bodytype / Gender
    const metaParts = [];
    if (has(N.level)) metaParts.push(`Level: ${N.level}`);
    if (has(N.race)) metaParts.push(`Race: ${N.race}`);
    if (has(N.class)) metaParts.push(`Class: ${N.class}`);
    if (has(N.bodytype)) metaParts.push(`Bodytype: ${N.bodytype}`);
    if (has(N.gender)) metaParts.push(`Gender: ${genderLabel(N.gender)}`);
    if (metaParts.length) push(out, `<div class="section">${metaParts.join(' | ')}</div>`);
  
    // HP, Mana, Size
    const stats = [];
    if (has(N.hp)) stats.push(`HP: ${N.hp}`);
    if (has(N.mana)) stats.push(`Mana: ${N.mana}`);
    if (has(N.size)) stats.push(`Size: ${N.size}`);
    if (stats.length) push(out, `<div class="section">${stats.join(' | ')}</div>`);
  
    // Regen rates
    const regen = [];
    if (has(N.hp_regen_rate)) regen.push(`HP Regen: ${N.hp_regen_rate}`);
    if (has(N.mana_regen_rate)) regen.push(`Mana Regen: ${N.mana_regen_rate}`);
    if (regen.length) push(out, `<div class="section">${regen.join(' | ')}</div>`);
  
    // Damage range
    if (has(N.mindmg) || has(N.maxdmg)) {
      push(out, `<div class="section">Damage: ${N.mindmg || 0} - ${N.maxdmg || '?'}</div>`);
    }
  
    // Attack metrics
    const combatStats = [];
    if (has(N.ATK)) combatStats.push(`ATK: ${N.ATK}`);
    if (has(N.AC)) combatStats.push(`AC: ${N.AC}`);
    if (has(N.Accuracy)) combatStats.push(`Accuracy: ${N.Accuracy}`);
    if (has(N.slow_mitigation)) combatStats.push(`Slow Mitigation: ${N.slow_mitigation}`);
    if (combatStats.length) push(out, `<div class="section">${combatStats.join(' | ')}</div>`);
  
    // Attack delay / speed
    if (has(N.attack_delay) || has(N.attack_speed)) {
      const delay = has(N.attack_delay) ? `${N.attack_delay} ms delay` : '';
      const speed = has(N.attack_speed) ? `Speed Multiplier: ${N.attack_speed}` : '';
      push(out, `<div class="section">${[delay, speed].filter(Boolean).join(' | ')}</div>`);
    }
  
    // Melee types
    if (has(N.prim_melee_type) || has(N.sec_melee_type)) {
      const prim = has(N.prim_melee_type) ? `Primary: ${N.prim_melee_type}` : '';
      const sec = has(N.sec_melee_type) ? `Secondary: ${N.sec_melee_type}` : '';
      push(out, `<div class="section">Melee: ${[prim, sec].filter(Boolean).join(' / ')}</div>`);
    }
  
    // Speed
    if (has(N.runspeed)) push(out, `<div class="section">Run Speed: ${N.runspeed}</div>`);
  
    // Special Abilities
    if (has(N.special_abilities)) {
      push(out, `<div class="section"><span class="label">Special Abilities:</span> ${N.special_abilities}</div>`);
    }
  
    return out.join('');
  }
  
  function genderLabel(gender) {
    switch (gender) {
      case 0: return 'Male';
      case 1: return 'Female';
      case 2: return 'Neuter';
      default: return 'Unknown';
    }
  }

  function renderTooltip(data, type) {
    switch (type) {
      case 'item':  return renderItem(data);
      case 'spell': return renderSpell(data);
      case 'npc':   return renderNpc(data);
      default:      return `<div>Unknown type: ${type}</div>`;
    }
  }

  function showTooltip(type, id, event) {
    ensureTooltipEl();
    const cacheKey = `${type}_${id}`;
    const show = (data) => {
      tooltipEl.innerHTML = renderTooltip(data, type);
      tooltipEl.style.opacity = 1;
      positionTooltip(event);
    };

    if (cache.has(cacheKey)) {
      show(cache.get(cacheKey));
    } else {
      fetch(`/api/${type}/${id}`)
        .then(res => res.json())
        .then(data => {
          cache.set(cacheKey, data);
          show(data);
        });
    }
  }

  function positionTooltip(event) {
    const rect = tooltipEl.getBoundingClientRect();
    const scrollX = window.scrollX || window.pageXOffset;
    const scrollY = window.scrollY || window.pageYOffset;
  
    let x = event.clientX + 12 + scrollX;
    let y = event.clientY + 12 + scrollY;
  
    if (x + rect.width > window.innerWidth + scrollX) {
      x = event.clientX - rect.width - 12 + scrollX;
    }
    if (y + rect.height > window.innerHeight + scrollY) {
      y = event.clientY - rect.height - 12 + scrollY;
    }
  
    tooltipEl.style.left = `${x}px`;
    tooltipEl.style.top = `${y}px`;
  }

  function hideTooltip() {
    if (tooltipEl) tooltipEl.style.opacity = 0;
  }

  function init() {
    ensureTooltipEl();
    document.querySelectorAll(config.selector).forEach(el => {
      const type = el.dataset.type;
      const id = el.dataset.id;
      if (!type || !id) return;

      el.addEventListener('mouseenter', e => showTooltip(type, id, e));
      el.addEventListener('mousemove', positionTooltip);
      el.addEventListener('mouseleave', hideTooltip);
    });
  }

  document.addEventListener('DOMContentLoaded', init);

  return {
    init,
    showTooltip,
    hideTooltip
  };
})();
