# Integration with the autonomous-agent-orchestration pipeline

This kanban board is a **mirror** of the orchestration engine's view of work.
The engine is authoritative for *what to do*; the board is a visual surface
operators can scan, edit by hand, and commit back as a proposal.

## Data flow

```
sources ──► scouts ──► intake ──► TriageEngine
                                    │
                                    ├─► Hermes Kanban (state-of-record)
                                    │
                                    └─► kanban/board.json (visual surface)
                                              │
                                              ▼
                                     index.html (operator view)
```

## Single integration point

The board is one file: `kanban/board.json`. Anything that needs to
"touch the board" should:

1. Read the file with `python3 kanban/cli.py show` or by parsing it directly.
2. Mutate the JSON (or hand-author edits).
3. Pipe the new file into `python3 kanban/cli.py apply` (which validates
   before writing).
4. `git add kanban/board.json && git commit && git push`.

The engine's `engine/kanban_store.py` already wraps Hermes Kanban calls.
Add a thin subscriber that, after a successful write to Hermes Kanban,
serializes the affected card(s) and pipes them into `kanban/cli.py apply`.

## Wiring example

```python
# engine/integrations/board_mirror.py
import json, subprocess, sys
from pathlib import Path

KANBAN = Path(__file__).resolve().parents[2] / "kanban"

def mirror(card: dict) -> None:
    board_file = KANBAN / "board.json"
    board = json.loads(board_file.read_text())
    # upsert by id
    cards = board.setdefault("cards", [])
    for i, existing in enumerate(cards):
        if existing.get("id") == card["id"]:
            cards[i] = {**existing, **card}
            break
    else:
        cards.append(card)
    # validate + write
    p = subprocess.run(
        [sys.executable, str(KANBAN / "cli.py"), "apply"],
        input=json.dumps(board, indent=2).encode(),
        check=True,
    )
```

## What the operator sees

- **Engine changes** → card appears/moves in `board.json` → next page load
  shows the new state.
- **Operator edits in the browser** → JSON export → `cli.py apply` → commit.
- **Human gate** → the existing `proposal_actions.py` flow. Adding a
  kanban mirror step is a one-line integration once the engine's
  `kanban_store.py` accepts subscribers.

## Why a separate file?

- The Hermes Kanban is a SQLite database (`kanban.db`) — fast, queryable,
  not diff-friendly. Operators want diffs.
- The static board is **read-first**: a single JSON file you can review in
  a PR. The engine keeps its real state, the board keeps the operator's view.
- If they ever drift, the engine wins (the board is a mirror). A nightly
  diff job can surface drift to the operator.
