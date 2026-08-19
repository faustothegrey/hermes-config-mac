"""Rebar Phase 1 — A5 material-change log (Task M1).

Append-only log of changes to the three evidence-identity components that
define an A5/A6 stable window:  normalizer | capability | comparator.

Discipline (from the frozen Phase-1 plan and the Feasibility Falsification
Program §6):
  * Materiality is declared AT COMMIT TIME, not reconstructed later.
  * Ratchet: review MAY upgrade non-material -> material; it MUST NOT
    downgrade material -> non-material to rescue an active evidence window.
  * The log is append-only. A reclassification is recorded as a new
    amendment record; prior records are never mutated or deleted.
  * M1 MUST be initialized (start timestamp recorded) BEFORE the first
    Phase-1 commit that touches any of the three components. `log_metadata.json`
    carries `log_started_at` as the proof that logging preceded the changes.

Storage lives beside this module by default; override with env `M1_DIR`
(used by the tests) to point at a scratch directory.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib

COMPONENTS = ("normalizer", "capability", "comparator")
SCHEMA = "m1.1"
_HERE = pathlib.Path(__file__).resolve().parent


def _dir() -> pathlib.Path:
    return pathlib.Path(os.environ["M1_DIR"]) if os.environ.get("M1_DIR") else _HERE


def _log_path() -> pathlib.Path:
    return _dir() / "material_change_log.jsonl"


def _meta_path() -> pathlib.Path:
    return _dir() / "log_metadata.json"


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def init(force: bool = False) -> dict:
    """Create the log metadata (records log_started_at) and an empty log."""
    meta_path = _meta_path()
    if meta_path.exists() and not force:
        raise SystemExit(f"already initialized: {meta_path}")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"schema": SCHEMA, "log_started_at": _utc_now()}
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    log_path = _log_path()
    if not log_path.exists():
        log_path.write_text("")
    return meta


def _read_entries() -> list[dict]:
    log_path = _log_path()
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def _append_record(rec: dict) -> dict:
    with _log_path().open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def append(component: str, material: bool, rationale: str,
           entry_id: str | None = None) -> dict:
    """Append a new material-change declaration."""
    if component not in COMPONENTS:
        raise ValueError(f"component must be one of {COMPONENTS}, got {component!r}")
    if not isinstance(material, bool):
        raise ValueError("material must be a bool declared at commit time")
    if not rationale or not rationale.strip():
        raise ValueError("rationale is required")
    if not _meta_path().exists():
        raise RuntimeError(
            "log not initialized; run `init` BEFORE the first relevant commit")
    n = len(_read_entries())
    rec = {
        "id": entry_id or f"mc-{n + 1:04d}",
        "date": _utc_now(),
        "component": component,
        "material": material,
        "rationale": rationale.strip(),
    }
    return _append_record(rec)


def reclassify(entry_id: str, material: bool, rationale: str) -> dict:
    """Reclassify an existing entry's materiality, enforcing the ratchet.

    Allowed:   non-material -> material (upgrade).
    Forbidden: material -> non-material (downgrade) — raises ValueError.
    Recorded as an append-only amendment; original record is preserved.
    """
    entries = _read_entries()
    target = next((e for e in entries if e["id"] == entry_id), None)
    if target is None:
        raise KeyError(entry_id)
    current = effective_material(entry_id)
    if current is True and material is False:
        raise ValueError(
            "ratchet violation: cannot downgrade material -> non-material")
    if current == material:
        return target  # no-op
    amend = {
        "id": f"{entry_id}-amend-{_utc_now()}",
        "date": _utc_now(),
        "component": target["component"],
        "material": material,
        "rationale": rationale.strip(),
        "amends": entry_id,
        "prior_material": current,
    }
    return _append_record(amend)


def effective_material(entry_id: str) -> bool | None:
    """Latest effective materiality of an entry after any amendments."""
    value = None
    for e in _read_entries():
        if e["id"] == entry_id or e.get("amends") == entry_id:
            value = e["material"]
    return value


def _cli(argv=None) -> int:
    p = argparse.ArgumentParser(description="Rebar A5 material-change log (M1)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").add_argument("--force", action="store_true")
    a = sub.add_parser("append")
    a.add_argument("component", choices=COMPONENTS)
    a.add_argument("material", choices=["material", "non-material"])
    a.add_argument("rationale")
    r = sub.add_parser("reclassify")
    r.add_argument("entry_id")
    r.add_argument("material", choices=["material", "non-material"])
    r.add_argument("rationale")
    sub.add_parser("list")
    ns = p.parse_args(argv)
    if ns.cmd == "init":
        print(json.dumps(init(force=ns.force), indent=2))
    elif ns.cmd == "append":
        print(json.dumps(append(ns.component, ns.material == "material", ns.rationale)))
    elif ns.cmd == "reclassify":
        print(json.dumps(reclassify(ns.entry_id, ns.material == "material", ns.rationale)))
    elif ns.cmd == "list":
        for e in _read_entries():
            print(json.dumps(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
