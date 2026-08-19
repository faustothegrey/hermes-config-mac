# Rebar — Rebrand Decision (2026-07-27)

**Original name:** capability-reuse  
**New name:** Rebar (armatura in cemento armato)  
**Status:** ✅ Decided, ⏳ Deferred until Phase 1B stable  

## Why Rebar

Il tondino d'acciaio dentro il cemento armato. È ciò che tiene insieme la struttura quando il cemento (execute_code generativo) da solo non basta. Senza armatura, sotto tensione il cemento si spacca — Rebar è quello che impedisce all'agente di frantumarsi su operazioni ripetute e costose.

Metafora: invece di colare cemento nuovo ogni volta (generare codice da zero), Rebar inserisce l'armatura già pronta (la capability registrata) nel punto giusto.

## Costo del rename stimato

| Componente | Stima |
|---|---|
| Skill dir + SKILL.md + references interni | ~15 min |
| Plugin dir + file .py + import reciproci | ~20 min |
| Env var (CAPABILITY_REUSE_MODE, etc.) + registry | ~30 min |
| Peer sync (70 central, 128 runtime, 138) | ~40 min |
| Conformance + regression tests | ~20 min |
| **Totale** | **~2-5 ore** |

## Approccio (Way 2 — Graduale)

1. Skill dir + SKILL.md + references (oggi fattibile, basso rischio)
2. Plugin rename + fix import (.py, sys.path, `__init__`)
3. Registry rename + env var migrate
4. Peer sync (70 → 128 → 138) con verifica dopo ogni passo

Il vecchio nome "capability-reuse" sopravvive come riferimento storico in transcript e HMP exchange.

## Riferimenti

- [[Rebar Founding Intent and Tool-Use Contract]] — charter canonico: origine HMP/curl e contratto pre-tool
- [[Capability Reuse Protocol — v1.6]] (SKILL.md originale)
- Loop Engineering vs Capability-Reuse analysis (2026-07-27)
- GEPA Skill Evolution paper (arXiv:2507.19457)
