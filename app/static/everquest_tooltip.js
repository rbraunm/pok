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
  0:  [1 << 0,  "Charm"],
  1:  [1 << 1,  "Ear"],
  2:  [1 << 2,  "Head"],
  3:  [1 << 3,  "Face"],
  /* Ear 2 */
  5:  [1 << 5,  "Neck"],
  6:  [1 << 6, "Shoulders"],
  7:  [1 << 7,  "Arms"],
  8:  [1 << 8,  "Back"],
  9:  [1 << 9,  "Wrist"],
  /* Wrist 2 */
  11:  [1 << 11, "Range"],
  12:  [1 << 12, "Hands"],
  13:  [1 << 13, "Primary"],
  14:  [1 << 14, "Secondary"],
  15:  [1 << 15, "Finger"],
  /* Finger 2 */
  17:  [1 << 17, "Chest"],
  18:  [1 << 18, "Legs"],
  19:  [1 << 19, "Feet"],
  20:  [1 << 20, "Waist"],
  21:  [1 << 21, "PowerSource"],
  22:  [1 << 22, "Ammo"],
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

const RESIST_TYPES = {
  0: "Unresistable",
  1: "Magic",
  2: "Fire",
  3: "Cold",
  4: "Poison",
  5: "Disease",
  6: "Chromatic",
  7: "Prismatic",
  8: "Physical",
  9: "Corruption"
};

const SKILLS = {
  0: "1H Blunt",
  1: "1H Slashing",
  2: "2H Blunt",
  3: "2H Slashing",
  4: "Abjuration",
  5: "Alteration",
  6: "Apply Poison",
  7: "Archery",
  8: "Backstab",
  9: "Bind Wound",
  10: "Bash",
  11: "Block",
  12: "Brass Instruments",
  13: "Channeling",
  14: "Conjuration",
  15: "Defense",
  16: "Disarm",
  17: "Disarm Traps",
  18: "Divination",
  19: "Dodge",
  20: "Double Attack",
  21: "Dragon Punch",
  22: "Dual Wield",
  23: "Eagle Strike",
  24: "Evocation",
  25: "Feign Death",
  26: "Flying Kick",
  27: "Forage",
  28: "Hand to Hand",
  29: "Hide",
  30: "Kick",
  31: "Meditate",
  32: "Mend",
  33: "Offense",
  34: "Parry",
  35: "Pick Lock",
  36: "1H Piercing",
  37: "Riposte",
  38: "Round Kick",
  39: "Safe Fall",
  40: "Sense Heading",
  41: "Singing",
  42: "Sneak",
  43: "Specialize Abjure",
  44: "Specialize Alteration",
  45: "Specialize Conjuration",
  46: "Specialize Divination",
  47: "Specialize Evocation",
  48: "Pick Pockets",
  49: "Stringed Instruments",
  50: "Swimming",
  51: "Throwing",
  52: "Tiger Claw",
  53: "Tracking",
  54: "Wind Instruments",
  55: "Fishing",
  56: "Make Poison",
  57: "Tinkering",
  58: "Research",
  59: "Alchemy",
  60: "Baking",
  61: "Tailoring",
  62: "Sense Traps",
  63: "Blacksmithing",
  64: "Fletching",
  65: "Brewing",
  66: "Alcohol Tolerance",
  67: "Begging",
  68: "Jewelry Making",
  69: "Pottery",
  70: "Percussion Instruments",
  71: "Intimidation",
  72: "Berserking",
  73: "Taunt",
  74: "Frenzy",
  75: "Remove Trap",
  76: "Triple Attack",
  77: "2H Piercing"
}


function decodeRaces(raceBitmask) {
  const allRaceMask = Object.values(RACE_BITMASK).reduce((sum, mask) => sum | mask, 0);
  if ((raceBitmask & allRaceMask) === allRaceMask) return 'Any';

  return Object.entries(RACE_BITMASK)
    .filter(([_, mask]) => (raceBitmask & mask) !== 0)
    .map(([name]) => name)
    .join(' ') || 'None';
}

const SIZE_LABELS = ['Tiny', 'Small', 'Medium', 'Large', 'Giant', 'Massive', 'Colossal'];

function formatSize(size) {
  return (size != null && SIZE_LABELS[size]) ? SIZE_LABELS[size] : 'Unknown';
}

function formatDuration(totalSeconds) {
  totalSeconds = Math.round(Number(totalSeconds)/1000);
  if (!totalSeconds || totalSeconds <= 0) return 'Instant';

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (seconds > 0) parts.push(`${seconds}s`);

  return parts.join(' ');
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

  span.eqtooltip { cursor: pointer !important; }
  
  .eqtooltip-container .name            { font-size: 18px !important; font-weight: 700 !important; margin-bottom: 2px !important; }
  .eqtooltip-container .flags           { color: #E0DFDB !important; }
  .eqtooltip-container .section         { display: block !important; margin: 2px 0 !important; line-height: 1.4 !important; }
  .eqtooltip-container .label           { font-weight: 700 !important; }
  .eqtooltip-container .stat-heroic     { color: #6cf !important; }
  .eqtooltip-container .effect          { color: #FFDF00 !important; }
  .eqtooltip-container .spell-wrapper   { margin-left: 44px !important; position: relative !important; }
  .eqtooltip-container .icon-container  { position: absolute !important; overflow: hidden !important; top: 0px !important; left: -42px !important; width: 40px !important; height: 40px !important; padding: 0 !important; background-origin: border-box !important; background-clip: padding-box, border-box !important; border: 2px solid transparent !important; border-radius: 4px !important; border-image: linear-gradient(135deg, #f9e49a, #d7b95d, #b68d27, #d7b95d, #f9e49a) 1 stretch !important; box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.85), 0 0 4px rgba(0, 0, 0, 0.6) !important; background-color: rgba(4, 16, 40, 0.85) !important; }
  .eqtooltip-container .spell-icon      { width: 40px !important; height: 40px !important; background-repeat: no-repeat !important; background-size: 240px 240px !important; image-rendering: pixelated !important; border: none !important; box-shadow: none !important; }
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
      if (has(D.skill)) parts.push(`Skill: ${SKILLS[D.skill] || D.skill}`);
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
      push(`<div class="section">WT: ${D.weight ? (D.weight / 10).toFixed(1) : ''} Size: ${formatSize(D.size)}</div>`);
    }
  
    // Class / Race
    if (has(D.classes)) push(`<div class="section"><span class="label">Class:</span> ${decodeClasses(parseInt(D.classes, 10))}</div>`);
    if (has(D.races)) push(`<div class="section"><span class="label">Race:</span> ${decodeRaces(parseInt(D.races, 10))}</div>`);
  
    // Augmentation Slots / Slot Info
    if (has(D.slotinfo)) push(`<div class="section">${decodeRaces(parseInt(D.slotinfo, 10))}</div>`);
  
    return out.join('');
  }

  function renderSpell(S) {
    const has = v => v !== undefined && v !== null && v !== '';
    let iconHTML = '';

    if (has(S.icon)) {
      const iconId = parseInt(S.icon, 10);
      const ICON  = 40;
      const COLS  = 6;
      const CELLS = 36;

      const sheet = Math.floor((iconId - 1) / CELLS) + 1;
      const idx   = (iconId - 1) % CELLS;
      const col   = idx % COLS;
      const row   = Math.floor(idx / COLS);

      const x = -(col * ICON);
      const y = -(row * ICON);

      iconHTML = `
        <div class="icon-container">
          <div class="spell-icon"
              style="
                background-image: url('/static/img/icons/spells0${sheet}.png') !important;
                background-position: ${x}px ${y}px !important;
                background-size: auto !important;   /* never scale the sheet   */
              ">
          </div>
        </div>
      `;
    }

    const parts = [];
    parts.push(`<div class="name">${S.name}</div>`);
    if (has(S.spell_category)) parts.push(`<div class="section"><strong>Type:</strong> ${S.spell_category}</div>`);
    if (has(S.skill))          parts.push(`<div class="section">Skill: ${SKILLS[S.skill] || S.skill}</div>`);
    if (has(S.mana))           parts.push(`<div class="section">Mana: ${S.mana}</div>`);
    if (has(S.cast_time))      parts.push(`<div class="section">Cast Time: ${formatDuration(S.cast_time)}</div>`);
    if (has(S.recast_time))    parts.push(`<div class="section">Recast Time: ${formatDuration(S.recast_time)}</div>`);
    if (has(S.recovery_time))  parts.push(`<div class="section">Recovery Time: ${formatDuration(S.recovery_time)}</div>`);
    if (has(S.targettype))     parts.push(`<div class="section">Target: ${S.targettype}</div>`);
    if (has(S.range)) {
      let r = `Range: ${S.range}`;
      if (has(S.aoerange)) r += ` (AE: ${S.aoerange})`;
      parts.push(`<div class="section">${r}</div>`);
    }
    if (has(S.buffduration))   parts.push(`<div class="section">Duration: ${formatDuration(S.buffduration)}</div>`);
    if (has(S.resisttype))     parts.push(`<div class="section">Resist: ${RESIST_TYPES[S.resisttype]}</div>`);
    if (has(S.HateAdded))      parts.push(`<div class="section">Hate: ${S.HateAdded} + ${S.bonushate || 0} bonus</div>`);
    if (has(S.you_cast))       parts.push(`<div class="section">You Cast: ${S.you_cast}</div>`);
    if (has(S.cast_on_you))    parts.push(`<div class="section">On You: ${S.cast_on_you}</div>`);
    if (has(S.cast_on_other))  parts.push(`<div class="section">On Other: ${S.cast_on_other}</div>`);
    if (has(S.spell_fades))    parts.push(`<div class="section">Wears Off: ${S.spell_fades}</div>`);

    return `${iconHTML}<div class="spell-wrapper">${parts.join('')}</div>`;
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
