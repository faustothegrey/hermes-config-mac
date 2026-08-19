"""Rebar Phase 1 — A5 convergence gate (Task M2).

Consumes the append-only material-change log (Task M1) and decides whether at
least one COMPLETE stable evidence window exists: a window during which none of
the three evidence-identity components (normalizer | capability | comparator)
had a *material* change.

Falsifiable discipline (frozen Phase-1 plan / Feasibility Program §6.2):
  * A window is [start, end] (end may be None = "open, up to now").
  * The window is VOIDED if any component has an EFFECTIVE-material change whose
    timestamp falls within (start, end]. Effective materiality respects the M1
    ratchet (amendments: non-material -> material upgrades count; forbidden
    downgrades never happen).
  * "Converged" == at least one non-voided window is demonstrated.
  * Reclassification may only make a window MORE voided, never less — we never
    redefine materiality to force convergence. This module only READS the log;
    it cannot mutate materiality.
  * The evidence identity is normalizer x capability x comparator; a change to
    ANY of the three voids the window.

This module makes no network calls and never touches plugin/ code.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import material_change_log as m1  # noqa: E402

COMPONENTS = m1.COMPONENTS


def _parse(ts: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(ts)


def material_changes_in_window(start: str, end: str | None) -> list[dict]:
    """Return effective-material changes whose date is in (start, end].

    An entry counts if its EFFECTIVE materiality (after amendments) is True and
    its own timestamp lies in the window. Amendment records carry their own
    date; original records that were later upgraded count at the ORIGINAL
    record's date (the change physically happened then).
    """
    entries = m1._read_entries()
    start_dt = _parse(start)
    end_dt = _parse(end) if end else None

    # Build effective materiality per base id.
    base_ids = [e["id"] for e in entries if "amends" not in e]
    hits = []
    for base_id in base_ids:
        if m1.effective_material(base_id) is not True:
            continue
        base = next(e for e in entries if e["id"] == base_id)
        ev_dt = _parse(base["date"])
        if ev_dt > start_dt and (end_dt is None or ev_dt <= end_dt):
            hits.append(base)
    return hits


def evaluate_window(start: str, end: str | None) -> dict:
    """Evaluate a single candidate window.

    Returns {converged: bool, voided_by: [...], window: {...}}.
    converged True == the window is stable (no material change inside it).
    """
    hits = material_changes_in_window(start, end)
    return {
        "converged": len(hits) == 0,
        "voided_by": [
            {"id": h["id"], "component": h["component"], "date": h["date"]}
            for h in hits
        ],
        "window": {"start": start, "end": end},
        "components_tracked": list(COMPONENTS),
    }


def _cli(argv=None) -> int:
    p = argparse.ArgumentParser(description="Rebar A5 convergence gate (M2)")
    p.add_argument("--start", required=True, help="ISO window start")
    p.add_argument("--end", default=None, help="ISO window end (default: open)")
    ns = p.parse_args(argv)
    result = evaluate_window(ns.start, ns.end)
    print(json.dumps(result, indent=2))
    return 0 if result["converged"] else 2


if __name__ == "__main__":
    raise SystemExit(_cli())
