#!/usr/bin/env python3
"""
kanban/cli.py — read/write board.json for the hermes-multi-agent-workflow kanban.

Subcommands
  validate   - Check board.json against the schema
  show       - Print board.json to stdout
  add        - Add a card from --json (full card object) or flags
  move       - Move a card to a different column (--id, --to)
  apply      - Replace board.json from stdin (used by the engine bridge)
  preflight  - Verify the file is clean for a commit (JSON parses, no secrets)

Examples
  python3 kanban/cli.py validate
  python3 kanban/cli.py show | jq .
  python3 kanban/cli.py move --id c_seed_intake --to in_progress
  python3 kanban/cli.py add --title "Review" --description "PR review" --column todo
  python3 kanban/cli.py apply < new-board.json
"""

from __future__ import annotations
import argparse, datetime, json, re, sys, pathlib
from typing import Any

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOARD = ROOT / "kanban" / "board.json"
VALID_COLUMNS = {"todo", "in_progress", "done"}
ID_RE = re.compile(r"^[a-zA-Z0-9_]{1,64}$")


def load() -> dict:
    with open(BOARD, "r", encoding="utf-8") as f:
        return json.load(f)


def save(b: dict) -> None:
    b["schema_version"] = b.get("schema_version", 1)
    with open(BOARD, "w", encoding="utf-8") as f:
        json.dump(b, f, indent=2, ensure_ascii=False)
        f.write("\n")


def validate(b: dict) -> list[str]:
    errs: list[str] = []
    for k in ("schema_version", "title", "columns", "cards"):
        if k not in b:
            errs.append(f"missing top-level key: {k}")
    cols = {c.get("id") for c in b.get("columns", [])}
    for req in ("todo", "in_progress", "done"):
        if req not in cols:
            errs.append(f"missing required column id: {req}")
    for i, c in enumerate(b.get("cards", [])):
        if not c.get("id") or not ID_RE.match(c["id"]):
            errs.append(f"card[{i}] id invalid: {c.get('id')!r}")
        if not c.get("title"):
            errs.append(f"card[{i}] title missing")
        if c.get("column") not in VALID_COLUMNS:
            errs.append(f"card[{i}] column invalid: {c.get('column')!r}")
    return errs


def cmd_validate(_a) -> int:
    b = load()
    errs = validate(b)
    if errs:
        for e in errs: print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print(f"✓ board.json valid ({len(b.get('cards', []))} cards, {len(b.get('columns', []))} columns)")
    return 0


def cmd_show(_a) -> int:
    json.dump(load(), sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


def cmd_add(a) -> int:
    b = load()
    if a.json:
        try:
            new = json.loads(a.json)
        except json.JSONDecodeError as e:
            print(f"✗ --json invalid: {e}", file=sys.stderr); return 1
    else:
        new = {}
    if not new.get("title") and a.title:
        new["title"] = a.title
    if not new.get("title"):
        print("✗ title required (use --title or --json)", file=sys.stderr); return 1
    new.setdefault("id", f"c_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}_{len(b.get('cards', [])) + 1:03d}")
    new.setdefault("description", a.description or "")
    new.setdefault("assignee", a.assignee or "")
    new.setdefault("due_date", a.due or None)
    new.setdefault("column", a.column or "todo")
    new.setdefault("subtasks", [])
    new.setdefault("order", (max((c.get("order", 0) for c in b.get("cards", [])), default=0)) + 1)
    new["updated_at"] = _now()
    if new["column"] not in VALID_COLUMNS:
        print(f"✗ column must be one of {sorted(VALID_COLUMNS)}", file=sys.stderr); return 1
    b.setdefault("cards", []).append(new)
    save(b)
    print(f"✓ added {new['id']} → {new['column']}")
    return 0


def cmd_move(a) -> int:
    b = load()
    if a.to not in VALID_COLUMNS:
        print(f"✗ --to must be one of {sorted(VALID_COLUMNS)}", file=sys.stderr); return 1
    for c in b.get("cards", []):
        if c.get("id") == a.id:
            c["column"] = a.to
            c["updated_at"] = _now()
            save(b); print(f"✓ moved {a.id} → {a.to}"); return 0
    print(f"✗ card id not found: {a.id}", file=sys.stderr); return 1


def cmd_apply(_a) -> int:
    raw = sys.stdin.read()
    try:
        b = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"✗ stdin invalid JSON: {e}", file=sys.stderr); return 1
    errs = validate(b)
    if errs:
        for e in errs: print(f"  ✗ {e}", file=sys.stderr); return 1
    b["updated_at"] = _now()
    save(b); print(f"✓ applied board.json ({len(b.get('cards', []))} cards)"); return 0


def cmd_preflight(_a) -> int:
    b = load()
    raw = json.dumps(b, indent=2, ensure_ascii=False)
    if any(s in raw.lower() for s in ("api_key", "password", "secret", "bearer ")):
        print("✗ possible secret-like string in board.json", file=sys.stderr); return 1
    errs = validate(b)
    if errs:
        for e in errs: print(f"  ✗ {e}", file=sys.stderr); return 1
    print("✓ preflight passed"); return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Hermes Multi-Agent Workflow kanban CLI")
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("validate").set_defaults(fn=cmd_validate)
    sp.add_parser("show").set_defaults(fn=cmd_show)
    pa = sp.add_parser("add"); pa.add_argument("--title"); pa.add_argument("--description"); pa.add_argument("--assignee")
    pa.add_argument("--due"); pa.add_argument("--column", default="todo"); pa.add_argument("--json"); pa.set_defaults(fn=cmd_add)
    pm = sp.add_parser("move", help="Move a card to a different column")
    pm.add_argument("--id", required=True); pm.add_argument("--to", required=True); pm.set_defaults(fn=cmd_move)
    sp.add_parser("apply", help="Replace board.json from stdin").set_defaults(fn=cmd_apply)
    sp.add_parser("preflight", help="Pre-commit validation").set_defaults(fn=cmd_preflight)
    a = p.parse_args(); return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
