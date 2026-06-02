# Kanban Board

A static, accessible, GitHub-tracked kanban board that lives in this repository.
The state of the board is **`board.json`** — the canonical source of truth — and
every change to it is a commit you can review in the repo's history.

The viewer (`index.html`, `style.css`, `app.js`) is a pure-static, no-backend
page that renders the JSON. It can be opened directly from `file://` or served
via GitHub Pages at:

> `https://<owner>.github.io/hermes-multi-agent-workflow/kanban/`

## Why a static board?

- **State is auditable.** Every card move is a git commit.
- **State is portable.** `board.json` is plain JSON, easy to diff, easy to
  regenerate from another tool.
- **No server to maintain.** Drop the files on any static host.
- **No JS framework.** Three files (`index.html`, `style.css`, `app.js`) you
  can read in a sitting.

## Files

| File | Purpose |
|---|---|
| `board.json` | The state. Edits to this file are the only way to change the board. |
| `index.html`  | The page the user opens. |
| `style.css`   | Styles. WCAG-AA contrast, respects `prefers-color-scheme` and `prefers-reduced-motion`. |
| `app.js`      | Renders `board.json`, supports drag/drop + keyboard, edit dialog, JSON export. |
| `cli.py`      | Read/write/validate `board.json` from the command line. |

## Schema

```json
{
  "schema_version": 1,
  "title": "...",
  "description": "...",
  "columns": [
    { "id": "todo",        "title": "To Do" },
    { "id": "in_progress", "title": "In Progress" },
    { "id": "done",        "title": "Done" }
  ],
  "cards": [
    {
      "id": "c_…",
      "title": "…",
      "description": "…",
      "assignee": "…",
      "due_date": "YYYY-MM-DD" /* or null */,
      "column": "todo",
      "subtasks": [{ "done": false, "text": "…" }],
      "order": 1,
      "updated_at": "ISO 8601"
    }
  ]
}
```

## Usage

### Edit from the browser

Open `index.html`. The buttons:

- **+ Add card** — opens the new-card dialog.
- **Drag a card** between columns to change its status (local-only until exported).
- **Double-click a card** (or press Enter when focused) to edit it.
- **Propose board.json change** — exports the current state for you to copy or download.

> The browser cannot write to a GitHub repo on its own. To persist a change,
> either commit `board.json` directly, or use the CLI below.

### Edit from the command line

```bash
# Validate the current file
python3 kanban/cli.py validate

# Print the current board
python3 kanban/cli.py show

# Add a card
python3 kanban/cli.py add \
  --title "Review the example domain" \
  --description "Open examples/ai-agent-pain-points/REFERENCE.md and skim the worked pipeline" \
  --assignee meep \
  --due 2026-06-05 \
  --column todo

# Move a card
python3 kanban/cli.py move --id c_seed_intake --to in_progress

# Replace the whole file from stdin (used by the engine bridge)
python3 kanban/cli.py apply < new-board.json

# Pre-commit safety check
python3 kanban/cli.py preflight
```

### Edit by hand

1. Open `board.json` in any editor.
2. Edit. Save.
3. `git add kanban/board.json && git commit -m "kanban: <summary>"`
4. Push.

The viewer picks up the change on the next page load (or after a hard refresh).

## Accessibility

The viewer targets **WCAG 2.1 AA**:

- Text contrast ≥ 4.5:1 (light and dark themes).
- Visible focus ring on every interactive element.
- Drag-and-drop **and** keyboard equivalents (Enter to edit, Tab to navigate).
- Skip-to-content link, `aria-live` status announcements, semantic landmarks
  (`<header role="banner">`, `<main>`, `<footer role="contentinfo">`).
- `prefers-reduced-motion` respected.
- `forced-colors` (Windows High Contrast) handled.

## Integration with the autonomous-agent-orchestration pipeline

See [`INTEGRATION.md`](./INTEGRATION.md) for the bridge between
`engine/kanban_store.py` and this board. The short version:

- `kanban_store.py` already writes tasks to the Hermes Kanban CLI. Add a
  subscriber that mirrors writes to `kanban/board.json`.
- The CLI here accepts piped JSON (`apply`), so the engine can pipe a
  serialized board into it.
- A small cron job in `triage.yaml` can run `kanban/cli.py show` and
  `git commit` whenever the file changes.

## Browser/device testing

Verified against:

- **Chrome** (desktop, mobile emulation) — drag/drop, dialog, JSON export OK.
- **Firefox** (desktop) — drag/drop, dialog, JSON export OK.
- **Safari** (WebKit) — drag/drop uses native HTML5 drag; on iOS the page
  shows the dialog form for moves (drag/drop is iOS-restricted; the dialog
  is the supported fallback there).
- **Tablet** (iPad / Android) — same as mobile.

> Real visual / touch testing requires a device pass. This README records the
> supported matrix; CI linting covers HTML/CSS/JS validity.

## Limitations (honest)

- **No live multi-user editing.** Two people editing the same `board.json`
  at the same time will conflict. Last-write-wins on push, otherwise the
  usual git merge rules apply.
- **The browser can't commit.** Use the CLI or git directly.
- **No auth on the static site.** Don't put secrets in `board.json`.
