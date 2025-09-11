/* =======================================================================
 * everquest_tooltip.js — ES module, auto-binding, nested (L1/L2) tooltips
 * ======================================================================= */

/* ------------------------------ Constants ------------------------------ */

const SLOT_BITMASKS = {
  0:[1<<0,"Charm"],1:[1<<1,"Ear"],2:[1<<2,"Head"],3:[1<<3,"Face"],
  5:[1<<5,"Neck"],6:[1<<6,"Shoulders"],7:[1<<7,"Arms"],8:[1<<8,"Back"],9:[1<<9,"Wrist"],
  11:[1<<11,"Range"],12:[1<<12,"Hands"],13:[1<<13,"Primary"],14:[1<<14,"Secondary"],15:[1<<15,"Finger"],
  17:[1<<17,"Chest"],18:[1<<18,"Legs"],19:[1<<19,"Feet"],20:[1<<20,"Waist"],21:[1<<21,"PowerSource"],22:[1<<22,"Ammo"],
};
function decodeSlots(bit){ if(!bit) return '';
  const all=Object.values(SLOT_BITMASKS).reduce((s,[m])=>s|m,0);
  if((bit & all)===all) return 'Any';
  return Object.values(SLOT_BITMASKS).filter(([m])=>bit&m).map(([,n])=>n).join(', ');
}

const CLASS_BITMASK={"WAR":1<<0,"CLR":1<<1,"PAL":1<<2,"RNG":1<<3,"SHD":1<<4,"DRU":1<<5,"MNK":1<<6,"BRD":1<<7,"ROG":1<<8,"SHM":1<<9,"NEC":1<<10,"WIZ":1<<11,"MAG":1<<12,"ENC":1<<13,"BST":1<<14,"BER":1<<15};
function decodeClasses(bit){const all=Object.values(CLASS_BITMASK).reduce((s,m)=>s|m,0); if((bit&all)===all) return 'Any';
  return Object.entries(CLASS_BITMASK).filter(([_,m])=>bit&m).map(([n])=>n).join(' ')||'None';
}

const RACE_BITMASK={"HUM":1<<0,"BAR":1<<1,"ERU":1<<2,"WEL":1<<3,"HIE":1<<4,"DEF":1<<5,"HEF":1<<6,"DWF":1<<7,"TRL":1<<8,"OGR":1<<9,"HFL":1<<10,"GNM":1<<11,"IKS":1<<12,"VAH":1<<13,"FRG":1<<14};
function decodeRaces(bit){const all=Object.values(RACE_BITMASK).reduce((s,m)=>s|m,0); if((bit&all)===all) return 'Any';
  return Object.entries(RACE_BITMASK).filter(([_,m])=>bit&m).map(([n])=>n).join(' ')||'None';
}

const RESIST_TYPES={0:"Unresistable",1:"Magic",2:"Fire",3:"Cold",4:"Poison",5:"Disease",6:"Chromatic",7:"Prismatic",8:"Physical",9:"Corruption"};
const SKILLS={0:"1H Blunt",1:"1H Slashing",2:"2H Blunt",3:"2H Slashing",4:"Abjuration",5:"Alteration",6:"Apply Poison",7:"Archery",8:"Backstab",9:"Bind Wound",10:"Bash",11:"Block",12:"Brass Instruments",13:"Channeling",14:"Conjuration",15:"Defense",16:"Disarm",17:"Disarm Traps",18:"Divination",19:"Dodge",20:"Double Attack",21:"Dragon Punch",22:"Dual Wield",23:"Eagle Strike",24:"Evocation",25:"Feign Death",26:"Flying Kick",27:"Forage",28:"Hand to Hand",29:"Hide",30:"Kick",31:"Meditate",32:"Mend",33:"Offense",34:"Parry",35:"Pick Lock",36:"1H Piercing",37:"Riposte",38:"Round Kick",39:"Safe Fall",40:"Sense Heading",41:"Singing",42:"Sneak",43:"Specialize Abjure",44:"Specialize Alteration",45:"Specialize Conjuration",46:"Specialize Divination",47:"Specialize Evocation",48:"Pick Pockets",49:"Stringed Instruments",50:"Swimming",51:"Throwing",52:"Tiger Claw",53:"Tracking",54:"Wind Instruments",55:"Fishing",56:"Make Poison",57:"Tinkering",58:"Research",59:"Alchemy",60:"Baking",61:"Tailoring",62:"Sense Traps",63:"Blacksmithing",64:"Fletching",65:"Brewing",66:"Alcohol Tolerance",67:"Begging",68:"Jewelry Making",69:"Pottery",70:"Percussion Instruments",71:"Intimidation",72:"Berserking",73:"Taunt",74:"Frenzy",75:"Remove Trap",76:"Triple Attack",77:"2H Piercing"};

const SIZE_LABELS=['Tiny','Small','Medium','Large','Giant','Massive','Colossal'];
function formatSize(s){return (s!=null&&SIZE_LABELS[s])?SIZE_LABELS[s]:'Unknown';}
function formatDuration(ms){ms=Math.round(Number(ms)/1000); if(!ms||ms<=0) return 'Instant'; const h=Math.floor(ms/3600), m=Math.floor((ms%3600)/60), s=ms%60;
  return [h?`${h}h`:null,m?`${m}m`:null,s?`${s}s`:null].filter(Boolean).join(' ');
}

// Fine-tune vertical alignment of the level-2 tooltip vs. the parent
const L2_ALIGN_NUDGE_Y = -2; // (reserved; not currently used)
const TOOLTIP_GAP = 12;
const ICON_OVERHANG = 52;

/* ------------------------------ Utils ------------------------------ */

function logMissingSpellName(kind, spellId, itemObj){
  try{console.error(`[EQTooltip] Missing ${kind} spell name for item tooltip`,{kind,spellId,itemId:itemObj.id||itemObj.ID,item:itemObj});}
  catch{console.error(`[EQTooltip] Missing ${kind} spell name`,kind,spellId,itemObj);}
}
function escapeHtml(str){const map={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}; return String(str??'').replace(/[&<>"']/g,ch=>map[ch]);}
function spellRef(id,name){ if(!id) return ""; const label=(name&&String(name).trim())||`#${id}`;
  return `<span class="eqtooltip" data-type="spell" data-id="${id}">${escapeHtml(label)}</span>`;
}

/* ------------------------------ Styles ------------------------------ */

(function injectTooltipStyles() {
  if (document.getElementById('eqtooltip-style')) return;
  const css = `
  .eqtooltip-container { visibility:hidden!important; opacity:0!important; transition:opacity .075s ease!important; }
  .eqtooltip-container.visible { visibility:visible!important; opacity:1!important; }
  .eqtooltip-container {
    all: initial;
    background:
      linear-gradient(rgba(4,16,40,.85), rgba(4,16,40,.85)),
      url('/static/img/everquest_tooltip_background.png') repeat;
    background-blend-mode: multiply!important; background-size: cover!important; background-position: center!important;
    border:2px solid transparent!important; border-radius:4px!important;
    background-origin:border-box; background-clip:padding-box, border-box;
    border-image: linear-gradient(135deg,#f9e49a,#d7b95d,#b68d27,#d7b95d,#f9e49a) 1 stretch!important;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.85), 0 0 4px rgba(0,0,0,.6)!important;
    max-width:350px!important; padding:6px 8px!important; color:#EAEAEA!important;
    font-family: Arial, Helvetica, sans-serif!important; font-size:12px!important; line-height:1.25!important;
    text-shadow:1px 1px 0 #000!important; text-align:left!important;
    position:absolute!important; pointer-events:auto; z-index:10000!important;
  }
  .eqtooltip-container.level2 { z-index:10001!important; }
  span.eqtooltip { cursor:pointer!important; }
  .eqtooltip-container .name { font-size:18px!important; font-weight:700!important; margin-bottom:2px!important; }
  .eqtooltip-container .flags { color:#E0DFDB!important; }
  .eqtooltip-container .section { display:block!important; margin:2px 0!important; line-height:1.4!important; }
  .eqtooltip-container .label { font-weight:700!important; }
  .eqtooltip-container .stat-heroic { color:#6cf!important; }
  .eqtooltip-container .effect { color:#FFDF00!important; }
  .eqtooltip-container .spell-wrapper { position:relative!important; padding-left:0!important; min-height:0!important; }
  .eqtooltip-container .icon-container {
    position:absolute!important; top:-2px!important; left:-52px!important; width:40px!important; height:40px!important; overflow:hidden!important;
    background-color:rgba(4,16,40,.85)!important; border:2px solid transparent!important; border-radius:4px!important;
    background-origin:border-box!important; background-clip:padding-box, border-box!important;
    border-image: linear-gradient(135deg,#e9d8a6,#c8aa6e,#a98b4d,#c8aa6e,#e9d8a6) 1 stretch!important;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.75), 0 0 3px rgba(0,0,0,.5)!important;
  }
  .eqtooltip-container .spell-icon {
    width:40px!important; height:40px!important; background-repeat:no-repeat!important;
    background-size:240px 240px!important; background-position:center center!important; image-rendering:pixelated!important;
    border:none!important; box-shadow:none!important;
  }`;
  const style = document.createElement('style');
  style.id = 'eqtooltip-style';
  style.textContent = css;
  document.head.appendChild(style);
})();

/* ------------------------------ State ------------------------------ */

const cache = new Map();
let tooltipEl = null;   // level 1 (item/npc)
let tooltipEl2 = null;  // level 2 (spell inside tooltip)

let config = { selector: '.eqtooltip', delay: 150 };

// Anchors & timers per level
let anchor1 = null, anchor2 = null;
let hideTimer1 = null, hideTimer2 = null;

/* ------------------------------ Core DOM ------------------------------ */

function ensureTooltipEls(){
  if(!tooltipEl){
    tooltipEl=document.createElement('div');
    tooltipEl.className='eqtooltip-container level1';
    document.body.appendChild(tooltipEl);
  }
  if(!tooltipEl2){
    tooltipEl2=document.createElement('div');
    tooltipEl2.className='eqtooltip-container level2';
    document.body.appendChild(tooltipEl2);
  }
}

function clearHideTimer(level){
  if(level===1 && hideTimer1){clearTimeout(hideTimer1);hideTimer1=null;}
  if(level===2 && hideTimer2){clearTimeout(hideTimer2);hideTimer2=null;}
}

function scheduleHide(level, delay = 150) {
  clearHideTimer(level);
  const fn = () => {
    const el = (level === 1 ? tooltipEl : tooltipEl2);
    if (el) el.classList.remove('visible');
    if (level === 1) {
      anchor1 = null;
      // ensure child never outlives parent
      if (tooltipEl2) {
        clearHideTimer(2);
        tooltipEl2.classList.remove('visible');
        anchor2 = null;
      }
    } else {
      anchor2 = null;
    }
  };
  if (level === 1) hideTimer1 = setTimeout(fn, delay);
  else hideTimer2 = setTimeout(fn, delay);
}

function has(v){ return v!==undefined && v!==null && v!=='' && v!==0 && v!=='0'; }

/* ------------------------------ Renderers ------------------------------ */

function renderItem(D){
  const out=[], push=h=>out.push(h);

  push(`<div class="name">${D.Name}</div>`);
  if(has(D.flags)) push(`<div class="flags">${D.flags}</div>`);

  if(has(D.slots)){
    const slotText=decodeSlots(parseInt(D.slots,10));
    if(slotText) push(`<div class="section"><span class="label">Slot:</span> ${slotText}</div>`);
  }

  if(has(D.skill)||has(D.delay)){
    const parts=[]; if(has(D.skill)) parts.push(`Skill: ${SKILLS[D.skill]||D.skill}`); if(has(D.delay)) parts.push(`Atk Delay: ${D.delay}`);
    push(`<div class="section">${parts.join(' ')}</div>`);
  }

  if(has(D.damage)||has(D.dmgBonus)||has(D.ac)){
    const parts=[]; if(has(D.damage)) parts.push(`DMG: ${D.damage}`); if(has(D.dmgBonus)) parts.push(`Dmg Bonus: ${D.dmgBonus}`); if(has(D.ac)) parts.push(`AC: ${D.ac}`);
    push(`<div class="section">${parts.join(' ')}</div>`);
  }

  if(has(D.placeable)) push(`<div class="section">${D.placeable}</div>`);

  const stats=['str','dex','sta','cha','wis','int','agi','hp','mana','endur'];
  const statParts=[];
  stats.forEach(stat=>{
    const cap=stat.toUpperCase();
    const baseVal=D[stat];
    const base=has(baseVal)?(baseVal>0?`+${baseVal}`:`${baseVal}`):'';
    const heroVal=D[`hero${cap}`];
    const hero=(has(heroVal)&&heroVal>0)?`<span class="stat-heroic">+${heroVal}</span>`:'';
    if(base||hero) statParts.push(`${cap}: ${base}${base&&hero?' ':''}${hero}`);
  });
  if(statParts.length) push(`<div class="section">${statParts.join(' ')}</div>`);

  const resists={fr:'SV FIRE',dr:'SV DISEASE',cr:'SV COLD',mr:'SV MAGIC',pr:'SV POISON'};
  const resistParts=[]; Object.entries(resists).forEach(([k,l])=>{ if(has(D[k])) resistParts.push(`${l}: +${D[k]}`);});
  if(resistParts.length) push(`<div class="section">${resistParts.join(' ')}</div>`);

  const misc=[]; if(has(D.attack)) misc.push(`Attack: +${D.attack}`); if(has(D.hpregen)) misc.push(`HP Regen: +${D.hpregen}`);
  if(has(D.manaregen)) misc.push(`Mana Regeneration: +${D.manaregen}`); if(has(D.clairvoyance)) misc.push(`Clairvoyance: +${D.clairvoyance}`);
  if(has(D.spelldamage)) misc.push(`Spell Damage: +${D.spelldamage}`); if(has(D.healamt)) misc.push(`Heal Amount: +${D.healamt}`);
  if(misc.length) push(`<div class="section">${misc.join(' ')}</div>`);

  if(has(D.reqlevel)) push(`<div class="section">Required level of ${D.reqlevel}.</div>`);
  if(has(D.reclevel)) push(`<div class="section">Recommended level ${D.reclevel}.</div>`);

  // Focus
  if (D.focuseffect && D.focuseffect !== -1) {
    const fname =
      (D.focusname && String(D.focusname).trim()) ||
      (D['focusname'] && String(D['focusname']).trim()) ||
      (D.focus_name && String(D.focus_name).trim()) ||
      null;
    if (!fname) logMissingSpellName('focus', D.focuseffect, D);
    const html = spellRef(D.focuseffect, fname);
    push(`<div class="section"><span class="label">Focus:</span> ${html}</div>`);
  }

  // Proc
  if (D.proceffect && D.proceffect !== -1) {
    const pname =
      (D.procname && String(D.procname).trim()) ||
      (D['procname'] && String(D['procname']).trim()) ||
      null;
    if (!pname) logMissingSpellName('proc', D.proceffect, D);
    const html = spellRef(D.proceffect, pname);
    push(`<div class="section"><span class="label">Proc:</span> ${html}</div>`);
  }

  // Click
  if (D.clickeffect && D.clickeffect !== -1) {
    const cname =
      (D.clickname && String(D.clickname).trim()) ||
      (D['clickname'] && String(D['clickname']).trim()) ||
      null;
    if (!cname) logMissingSpellName('click', D.clickeffect, D);
    const html = spellRef(D.clickeffect, cname);
    push(`<div class="section"><span class="label">Click:</span> ${html}</div>`);
  }
  // Bard Instrument
  if (D.bardeffect && D.bardeffect !== -1 && D.bardspellname) {
    const html = spellRef(D.bardeffect, D.bardspellname);
    push(`<div class="section"><span class="label">Bard:</span> ${html}</div>`);
  }


  if(has(D.weight)||has(D.size)){ push(`<div class="section">WT: ${D.weight?(D.weight/10).toFixed(1):''} Size: ${formatSize(D.size)}</div>`); }

  if(has(D.classes)) push(`<div class="section"><span class="label">Class:</span> ${decodeClasses(parseInt(D.classes,10))}</div>`);
  if(has(D.races)) push(`<div class="section"><span class="label">Race:</span> ${decodeRaces(parseInt(D.races,10))}</div>`);

  if(has(D.slotinfo)) push(`<div class="section">${decodeRaces(parseInt(D.slotinfo,10))}</div>`);

  return out.join('');
}

function renderSpell(S){
  const has=v=>v!==undefined && v!==null && v!=='';
  let iconHTML='';
  if(has(S.icon)){
    const iconId=parseInt(S.icon,10);
    const ICON=40,COLS=6,CELLS=36;
    const sheet=Math.floor((iconId-1)/CELLS)+1;
    const idx=(iconId-1)%CELLS, col=idx%COLS, row=Math.floor(idx/COLS);
    const x=-(col*ICON), y=-(row*ICON);
    iconHTML=`
      <div class="icon-container">
        <div class="spell-icon" style="
          background-image:url('/static/img/icons/spells0${sheet}.png') !important;
          background-position:${x}px ${y}px !important; background-size:auto !important;">
        </div>
      </div>`;
  }

  const parts=[];
  parts.push(`<div class="name">${S.name}</div>`);
  if(has(S.spell_category)) parts.push(`<div class="section"><strong>Type:</strong> ${S.spell_category}</div>`);
  if(has(S.skill))          parts.push(`<div class="section">Skill: ${SKILLS[S.skill]||S.skill}</div>`);
  if(has(S.mana))           parts.push(`<div class="section">Mana: ${S.mana}</div>`);
  if(has(S.cast_time))      parts.push(`<div class="section">Cast Time: ${formatDuration(S.cast_time)}</div>`);
  if(has(S.recast_time))    parts.push(`<div class="section">Recast Time: ${formatDuration(S.recast_time)}</div>`);
  if(has(S.recovery_time))  parts.push(`<div class="section">Recovery Time: ${formatDuration(S.recovery_time)}</div>`);
  if(has(S.targettype))     parts.push(`<div class="section">Target: ${S.targettype}</div>`);
  if(has(S.range)){ let r=`Range: ${S.range}`; if(has(S.aoerange)) r+=` (AE: ${S.aoerange})`; parts.push(`<div class="section">${r}</div>`); }
  if(has(S.buffduration))   parts.push(`<div class="section">Duration: ${formatDuration(S.buffduration)}</div>`);
  if(has(S.resisttype))     parts.push(`<div class="section">Resist: ${RESIST_TYPES[S.resisttype]}</div>`);
  if(has(S.HateAdded))      parts.push(`<div class="section">Hate: ${S.HateAdded} + ${S.bonushate||0} bonus</div>`);
  if(has(S.you_cast))       parts.push(`<div class="section">You Cast: ${S.you_cast}</div>`);
  if(has(S.cast_on_you))    parts.push(`<div class="section">On You: ${S.cast_on_you}</div>`);
  if(has(S.cast_on_other))  parts.push(`<div class="section">On Other: ${S.cast_on_other}</div>`);
  if(has(S.spell_fades))    parts.push(`<div class="section">Wears Off: ${S.spell_fades}</div>`);

  return `${iconHTML}<div class="spell-wrapper">${parts.join('')}</div>`;
}

function renderNpc(N){
  const out=[], push=h=>out.push(h);
  const fullName=N.lastname?`${N.name} ${N.lastname}`:N.name;
  push(`<div class="name">${fullName}</div>`);
  const meta=[]; if(has(N.level)) meta.push(`Level: ${N.level}`); if(has(N.race)) meta.push(`Race: ${N.race}`);
  if(has(N.class)) meta.push(`Class: ${N.class}`); if(has(N.bodytype)) meta.push(`Bodytype: ${N.bodytype}`); if(has(N.gender)) meta.push(`Gender: ${genderLabel(N.gender)}`);
  if(meta.length) push(`<div class="section">${meta.join(' | ')}</div>`);
  const stats=[]; if(has(N.hp)) stats.push(`HP: ${N.hp}`); if(has(N.mana)) stats.push(`Mana: ${N.mana}`); if(has(N.size)) stats.push(`Size: ${N.size}`);
  if(stats.length) push(`<div class="section">${stats.join(' | ')}</div>`);
  const regen=[]; if(has(N.hp_regen_rate)) regen.push(`HP Regen: ${N.hp_regen_rate}`); if(has(N.mana_regen_rate)) regen.push(`Mana Regen: ${N.mana_regen_rate}`);
  if(regen.length) push(`<div class="section">${regen.join(' | ')}</div>`);
  if(has(N.mindmg)||has(N.maxdmg)) push(`<div class="section">Damage: ${N.mindmg||0} - ${N.maxdmg||'?'}</div>`);
  const combat=[]; if(has(N.ATK)) combat.push(`ATK: ${N.ATK}`); if(has(N.AC)) combat.push(`AC: ${N.AC}`); if(has(N.Accuracy)) combat.push(`Accuracy: ${N.Accuracy}`); if(has(N.slow_mitigation)) combat.push(`Slow Mitigation: ${N.slow_mitigation}`);
  if(combat.length) push(`<div class="section">${combat.join(' | ')}</div>`);
  if(has(N.attack_delay)||has(N.attack_speed)){ const d=has(N.attack_delay)?`${N.attack_delay} ms delay`:''; const sp=has(N.attack_speed)?`Speed Multiplier: ${N.attack_speed}`:''; push(`<div class="section">${[d,sp].filter(Boolean).join(' | ')}</div>`); }
  if(has(N.prim_melee_type)||has(N.sec_melee_type)){ const p=has(N.prim_melee_type)?`Primary: ${N.prim_melee_type}`:''; const s=has(N.sec_melee_type)?`Secondary: ${N.sec_melee_type}`:''; push(`<div class="section">Melee: ${[p,s].filter(Boolean).join(' / ')}</div>`); }
  if(has(N.runspeed)) push(`<div class="section">Run Speed: ${N.runspeed}</div>`);
  if(has(N.special_abilities)) push(`<div class="section"><span class="label">Special Abilities:</span> ${N.special_abilities}</div>`);
  return out.join('');
}

function genderLabel(g){switch(g){case 0:return 'Male';case 1:return 'Female';case 2:return 'Neuter';default:return 'Unknown';}}

function renderTooltip(data,type){
  switch(type){
    case 'item': return renderItem(data);
    case 'spell': return renderSpell(data);
    case 'npc': return renderNpc(data);
    default: return `<div>Unknown type: ${type}</div>`;
  }
}

/* ------------------------------ Positioning ------------------------------ */

function positionTooltip(level) {
  const scrollX = window.scrollX || window.pageXOffset || 0;
  const scrollY = window.scrollY || window.pageYOffset || 0;
  const vpLeft   = scrollX + TOOLTIP_GAP;
  const vpTop    = scrollY + TOOLTIP_GAP;
  const vpRight  = scrollX + window.innerWidth  - TOOLTIP_GAP;
  const vpBottom = scrollY + window.innerHeight - TOOLTIP_GAP;

  if (level === 1) {
    if (!tooltipEl) return;
    const el = anchor1 || document.body;
    const ar = el.getBoundingClientRect();
    const tr = tooltipEl.getBoundingClientRect();

    // Try right of anchor
    let x = ar.right + TOOLTIP_GAP + scrollX;
    // If it overflows right, try left of anchor
    if (x + tr.width > vpRight) {
      const leftCandidate = ar.left - tr.width - TOOLTIP_GAP + scrollX;
      x = (leftCandidate >= vpLeft) ? leftCandidate : Math.max(vpLeft, vpRight - tr.width);
    }

    // Top aligned to anchor, then clamped to viewport
    let y = ar.top + scrollY;
    if (y + tr.height > vpBottom) y = Math.max(vpTop, vpBottom - tr.height);
    if (y < vpTop) y = vpTop;

    tooltipEl.style.left = `${x}px`;
    tooltipEl.style.top  = `${y}px`;
    return;
  }

  // level 2
  if (!tooltipEl2) return;

  const parentRect = tooltipEl.getBoundingClientRect();
  const tr2 = tooltipEl2.getBoundingClientRect();

  // Prefer right of parent with extra gutter for overhanging icon
  let x2 = parentRect.right + (TOOLTIP_GAP + ICON_OVERHANG) + scrollX;
  // If it overflows, flip to left of parent
  if (x2 + tr2.width > vpRight) {
    x2 = parentRect.left - tr2.width - TOOLTIP_GAP + scrollX;
    if (x2 < vpLeft) x2 = Math.max(vpLeft, vpRight - tr2.width);
  }

  // Top-align to parent tooltip, then clamp vertically
  let y2 = parentRect.top + scrollY;
  if (y2 + tr2.height > vpBottom) y2 = Math.max(vpTop, vpBottom - tr2.height);
  if (y2 < vpTop) y2 = vpTop;

  tooltipEl2.style.left = `${x2}px`;
  tooltipEl2.style.top  = `${y2}px`;
}

/* ------------------------------ Show / Hide ------------------------------ */

function _show(level, type, id, event) {
  ensureTooltipEls();

  // Clear any pending hide for the level we’re about to show
  clearHideTimer(level);

  // Remember the element we anchored on
  const el = event && event.target ? event.target.closest('.eqtooltip') : null;
  if (level === 1) {
    anchor1 = el || anchor1;

    // If we’re switching/refreshing the parent, kill any lingering child immediately
    if (tooltipEl2 && tooltipEl2.classList.contains('visible')) {
      clearHideTimer(2);
      tooltipEl2.classList.remove('visible');
      anchor2 = null;
    }
  } else {
    anchor2 = el || anchor2;
  }

  const box = (level === 1 ? tooltipEl : tooltipEl2);
  const cacheKey = `${type}_${id}`;

  const show = (data) => {
    try {
      box.innerHTML = renderTooltip(data, type);
    } catch (e) {
      console.error('[EQTooltip] render failed:', e, { type, id, data });
      const name = (data && (data.name || data.Name)) || `${type} #${id}`;
      box.innerHTML = `<div class="name">${escapeHtml(name)}</div>`;
    }

    if (level === 2) box.classList.add('level2'); else box.classList.remove('level2');
    box.classList.add('visible');

    // Position after layout
    requestAnimationFrame(() => positionTooltip(level));
  };

  if (cache.has(cacheKey)) {
    show(cache.get(cacheKey));
    return;
  }

  fetch(`/api/${type}/${id}`)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(data => {
      cache.set(cacheKey, data);
      show(data);
    })
    .catch(err => console.error('[EQTooltip] fetch failed:', err, { type, id }));
}

export function showTooltip(type,id,event){
  // If the trigger is inside level1 tooltip, route to level2; else level1
  const insideLevel1 = tooltipEl && (event?.target) && tooltipEl.contains(event.target);
  _show(insideLevel1 ? 2 : 1, type, id, event);
}

export function hideTooltip(level) {
  if (level === 1 || !level) {
    if (tooltipEl) tooltipEl.classList.remove('visible');
    anchor1 = null;
    if (tooltipEl2) {
      clearHideTimer(2);
      tooltipEl2.classList.remove('visible');
      anchor2 = null;
    }
  }
  if (level === 2 || !level) {
    if (tooltipEl2) tooltipEl2.classList.remove('visible');
    anchor2 = null;
  }
}

/* ------------------------------ Init / Events ------------------------------ */

// event delegation for hover in/out
function bindGlobalHoverHandlers() {
  document.addEventListener('mouseenter', (e) => {
    const el = e.target.closest('.eqtooltip');
    if (!el) return;
    const { type, id } = el.dataset;
    if (!type || !id) return;

    const insideLevel1 = tooltipEl && tooltipEl.contains(el);
    // entering a brand-new parent → hide any lingering level-2
    if (!insideLevel1 && tooltipEl2 && tooltipEl2.classList.contains('visible')) {
      clearHideTimer(2);
      tooltipEl2.classList.remove('visible');
      anchor2 = null;
    }

    clearHideTimer(insideLevel1 ? 2 : 1);
    _show(insideLevel1 ? 2 : 1, type, id, e);
  }, true); // capture

  document.addEventListener('mouseout', (e) => {
    const el = e.target.closest('.eqtooltip');
    if (!el) return;

    const to = e.relatedTarget;
    if (
      to &&
      (
        (tooltipEl  && (to === tooltipEl  || tooltipEl.contains(to))) ||
        (tooltipEl2 && (to === tooltipEl2 || tooltipEl2.contains(to)))
      )
    ) return;

    const insideLevel1 = tooltipEl && tooltipEl.contains(el);
    scheduleHide(insideLevel1 ? 2 : 1, 150);
  }, true);
}

// keep open while hovering the containers themselves
function bindContainerHoverGuards() {
  tooltipEl.addEventListener('mouseenter', () => { clearHideTimer(1); });
  tooltipEl.addEventListener('mouseleave', (e) => {
    if (e.relatedTarget && tooltipEl2 && tooltipEl2.contains(e.relatedTarget)) return;
    scheduleHide(1, 150);
  });

  tooltipEl2.addEventListener('mouseenter', () => { clearHideTimer(2); clearHideTimer(1); });
  tooltipEl2.addEventListener('mouseleave', (e) => {
    if (e.relatedTarget && tooltipEl && tooltipEl.contains(e.relatedTarget)) return;
    scheduleHide(2, 150);
  });

  const repro = () => {
    if (tooltipEl  && tooltipEl.classList.contains('visible'))  positionTooltip(1);
    if (tooltipEl2 && tooltipEl2.classList.contains('visible')) positionTooltip(2);
  };
  window.addEventListener('scroll', repro, { passive: true });
  window.addEventListener('resize', repro);
}

/* ---------- Auto-binding of .eqtooltip nodes (a11y + no double-bind) ---------- */

const BOUND = new WeakSet();

function onEqKeydown(e){
  // open on Enter/Space; close on Escape
  const el = e.currentTarget;
  const { type, id } = el.dataset;
  if (!type || !id) return;

  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    showTooltip(type, id, e);
  } else if (e.key === 'Escape') {
    hideTooltip();
  }
}

function bindEqEl(el){
  if (!el || BOUND.has(el)) return;
  BOUND.add(el);
  if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
  if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
  el.classList.add('eqtooltip--bound');
  el.addEventListener('keydown', onEqKeydown);
}

function scanAndBind(root = document){
  root.querySelectorAll('.eqtooltip[data-type][data-id]').forEach(bindEqEl);
}

function startAutoBinder(){
  // initial pass
  scanAndBind(document);

  // watch for new/changed nodes
  const mo = new MutationObserver((mutations) => {
    for (const m of mutations) {
      m.addedNodes.forEach((n) => {
        if (n.nodeType !== 1) return;
        if (n.matches?.('.eqtooltip')) bindEqEl(n);
        n.querySelectorAll?.('.eqtooltip').forEach(bindEqEl);
      });
      if (m.type === 'attributes' && m.target.matches?.('.eqtooltip')) bindEqEl(m.target);
    }
  });
  mo.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['data-id','data-type','class']
  });
}

/* ---------- Public init ---------- */

export function init() {
  ensureTooltipEls();
  bindGlobalHoverHandlers();
  bindContainerHoverGuards();
  startAutoBinder();
}

// auto-init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
  init();
}

// optional global for convenience
if (typeof window !== 'undefined') {
  window.EQTooltip = { init, showTooltip, hideTooltip };
}

export default { init, showTooltip, hideTooltip };