# Combat Sim -- Design Pass

Status: design pass. This is a starting point, not a bible. Everything here is open to
revision once implementation starts surfacing real constraints.

## Purpose

A class-based combat simulation module for PoK. A player configures an attacker (class,
level, stats, weapons) and a defender (an NPC or hand-entered stats), and the module runs
a Monte Carlo simulation of melee rounds to report DPS, hit distribution, and the
contribution of each mechanic (multi-attacks, avoidance, specials, procs).

Melee first. Spell/DoT damage is a later phase.

## Ground truth

The simulation models the EQEmu ruleset as configured in the database PoK is attached to.
Rules are read directly from the database at runtime -- never copied into code, config,
or fixtures. If the server operator changes a rule, the sim reflects it on the next run:

- `rule_values` -- combat-relevant server rules for the active ruleset.
- `skill_caps` -- per-class, per-level skill caps (offense, weapon skills, double attack,
  dual wield, defense, avoidance skills, specials).
- `items` -- weapon damage, delay, procs, stat contributions.
- `npc_types` -- defender level, class, AC, stats, and special abilities.

Where a mechanic is not driven by table data, the reference is EQEmu server behavior for
the emulated era. When server behavior is unclear or version-dependent, that is an open
question logged below, resolved empirically (in-game testing against the target server)
rather than by assumption.

### Prior art

The P99 community damage calculator demonstrates the feature surface a tool like this
covers: to-hit, AC mitigation, damage tables and caps, double attack, dual wield,
riposte/parry/dodge/block, class specials (e.g. backstab), critical hits, weapon procs,
haste, level-scaled skill caps, and Monte Carlo aggregation over many swing sets.

That tool is prior art only. This is a cleanroom effort: no code, formulas, tables, or
constants are taken from it. It defines the kind of questions the module must answer, not
the answers. It also targets P99's classic ruleset, which is not the ruleset of the
attached database.

## Feature surface (v1 target)

Attacker model:
- Class, level, STR/DEX/AGI, ATK from items and spells, haste percentage.
- Main hand and off hand weapons: damage, delay, proc effects.
- Skills either entered directly or auto-derived from `skill_caps` at the given level.

Defender model:
- Pick an NPC from `npc_types`, or enter level/class/AC/AGI/avoidance skills by hand.
- NPC-sourced values pre-fill the form and remain editable.

Round engine:
- To-hit and avoidance resolution (miss, riposte, parry, dodge, block).
- Mitigation and damage roll per landed hit, with class/level damage behavior.
- Multi-attack resolution: double attack, dual wield, and any ruleset-enabled extensions.
- Class specials where they change sustained DPS (backstab first; others staged).
- Weapon procs and their damage contribution.

Output:
- Sustained DPS as a distribution (mean plus spread over N simulated sets), not a single
  number.
- Breakdown by source: main hand, off hand, specials, procs.
- Hit outcome distribution: miss/avoid/land rates.

## Architecture sketch

Follows the existing PoK module pattern:

- `app/blueprints/CombatSim.py` -- Flask blueprint, form rendering, request handling.
  PascalCase filename to match the existing blueprint files.
- `app/api/models/combatSim/` -- the engine package:
  - Stat and rule loaders backed by `getDb()` (rules, skill caps, item lookup, NPC
    lookup). Loaders fail loudly when an expected rule or cap row is absent -- no
    defaulted constants masking a misconfigured ruleset.
  - Round engine: pure functions from (attackerState, defenderState, rules, RNG) to a
    resolved round. No DB access inside the engine; everything is loaded up front.
  - Simulation runner: seeds RNG, runs N sets of M rounds, aggregates.
- Determinism: the runner accepts an explicit RNG seed so any reported result is
  reproducible. Tests pin seeds.

Keeping the engine pure and DB-free at its core is the load-bearing decision: it makes
the math testable in isolation and keeps the ruleset swappable if PoK is ever pointed at
a different database.

## Where to begin

1. Rule and cap loaders: enumerate which `rule_values` and `skill_caps` rows the melee
   model actually needs, and load them live from the DB. This forces the first real
   contact with the attached ruleset and will surface gaps early.
2. Single-swing resolution: to-hit, avoidance, mitigation, damage roll for one main hand
   swing, warrior vs. warrior. Verified empirically against the target server before
   layering anything on top.
3. Multi-attack layer: double attack, dual wield.
4. Haste and delay handling; DPS aggregation over time.
5. First special: backstab. First proc handling.
6. Blueprint UI: form in, tables out. CSV export can ride the existing Exports pattern.

Each step lands as its own checkpoint. Step 2 is the keystone -- if single-swing math is
verified against the real server, everything above it is composition.

## Deferred (explicitly out of v1)

- Spell, DoT, and pet damage.
- Defensive simulation (incoming DPS / tanking view).
- Discipline and buff timelines (burst windows).
- Raid-context modifiers (debuff stacking on the defender).

## Open questions

- Which EQEmu release/era does the attached server run, and which combat-affecting
  custom rules differ from stock? Needs a `rule_values` audit as part of step 1.
- Damage bonus and damage table behavior for the active era -- confirm empirically before
  encoding.
- Whether NPC avoidance/mitigation values in `npc_types` are used as-is by the server or
  level-scaled at spawn. Determines whether the loader replicates scaling.
- How much of the attacker form should auto-populate from PoK's existing item/character
  models vs. stay manual in v1.
