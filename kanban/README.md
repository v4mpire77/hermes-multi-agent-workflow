# Kanban Board

A static, accessible, GitHub-tracked kanban board that lives in this repository.
The state of the board is **`board.json`** — the canonical source of truth — and
every change to it is a commit you can review in the repo's history.

The viewer (`index.html`, `style.css`, `app.js`) is a pure-static, no-backend
page that renders the JSON. It can be opened directly from `file://` or served
via GitHub Pages at:

> `https://<owner>.github.io/hermes-multi-agent-workflow/kanban/`

## Setup

The board is **zero-install for users** — open the URL. To run the test suite
or to host it under your own domain, see the steps below.

### 1. Just view it

Open the GitHub Pages URL in any modern browser. The page reads
`board.json` over HTTPS and renders. No build step.

### 2. Host it yourself

The board is three static files plus a JSON file. Drop them on any static
host (S3 + CloudFront, Netlify, Cloudflare Pages, GitHub Pages, a plain
Nginx box). There is **no backend, no API, no build**.

```bash
# Local dev
git clone https://github.com/<you>/hermes-multi-agent-workflow
cd hermes-multi-agent-workflow/kanban
python3 -m http.server 8765 --bind 127.0.0.1
# open http://127.0.0.1:8765/
```

### 3. Edit the board

Four options, in order of formality:

| | How | Persisted via | Best for |
|---|---|---|---|
| Browser dialog | "+ Add card" button on the page | Copy the exported JSON and commit it | Quick experiments |
| CLI | `python3 kanban/cli.py add --title "..."` | `git commit` | Scripting, CI, automation |
| Hand-edit | Open `board.json`, edit, save | `git commit` | One-off changes |
| Engine bridge | `engine/kanban_store.py` writes → subscriber mirrors to `board.json` | `git commit` (auto) | Multi-agent pipelines |

See the **Usage** section below for full CLI examples.

### 4. Run the tests

```bash
bash scripts/test-matrix.sh
```

This runs the unit + browser test matrix and writes the evidence report
to `kanban/tests/TEST_MATRIX.md`. See the **Browser/device testing**
section below for what is and is not covered.

### 5. Customize

The board's behavior is entirely in `board.json`, `index.html`, `style.css`,
and `app.js`. To add columns, change the `columns` array in `board.json` —
the viewer will pick them up on next load. To restyle, edit `style.css` —
it has CSS custom properties at the top for the column palette.

## Features

### View

- **Three columns by default** (To Do, In Progress, Done) — easy to extend
  by editing the `columns` array in `board.json`.
- **Cards** show title, description, assignee pill (`@user`), due-date pill
  (color-coded: red overdue, amber within 2 days, default otherwise), and
  a subtask checklist.
- **Live count** in the header (`3 cards loaded from board.json`) confirms
  the page parsed the file correctly.
- **Light + dark** by `prefers-color-scheme`. No toggle needed.

### Interact

- **Drag and drop** a card between columns to change its status. Visual
  feedback (`.dragging`, `.drop-target` highlights) confirms the move.
- **Double-click** a card (or press **Enter** when focused) to open the
  edit dialog — same dialog used for "+ Add card" and for editing.
- **+ Add card** opens the dialog with all fields blank, plus a Delete
  button hidden for new cards.
- **"Propose board.json change"** exports the current in-memory state as
  a copyable + downloadable JSON file. Commit it to persist.
- **Keyboard navigation** works throughout: Tab moves focus, Enter opens
  the dialog, focus rings are visible on every interactive element.

### Operate

- **Zero build, zero deps, zero backend.** Three files: HTML, CSS, JS.
  The JSON file is the only state.
- **No framework.** No React, no Vue, no bundler. Read the source in
  under five minutes.
- **No data leaves your machine** unless you commit and push. The page
  fetches `board.json` from wherever you host it.
- **Git history is the audit log.** Every change is a commit you can
  `git log` and `git blame`.

### Accessibility

- **WCAG 2.1 AA** color contrast in both light and dark themes.
- **Semantic landmarks** — `banner`, `main`, three `region`s, `contentinfo`.
- **Skip link** at the top of the page jumps focus past the header.
- **`aria-live`** status announcements for moves and errors.
- **Visible focus rings** on every interactive element.
- **Respects `prefers-reduced-motion`** — drag animations disabled when
  the user has motion sensitivity enabled.
- **Respects `forced-colors`** (Windows High Contrast) — fall back to
  system colors when active.
- **Touch-friendly** — the dialog form is the primary path on iOS Safari
  where HTML5 drag/drop is not supported.

### Integration

- The board's `board.json` is the **canonical source of truth** for the
  pipeline. A subscriber in `engine/kanban_store.py` mirrors engine
  state into the JSON file. See [`INTEGRATION.md`](./INTEGRATION.md).

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

> ⚠️ **Honest scope.** The full CI test matrix runs against a single engine
> (Camoufox, which is Firefox-based) at the daemon's default desktop
> viewport. The board is built with standards-track HTML5 / ARIA / CSS and
> should work in Chrome and Safari, but those are not empirically tested
> by this harness. See [`kanban/tests/TEST_MATRIX.md`](./tests/TEST_MATRIX.md)
> for the actual evidence — what ran, what passed, and the screenshots
> captured during the most recent run.

For drag/drop on iOS Safari (where HTML5 drag is not supported), the page
exposes the same edit dialog as a touch-friendly fallback. The dialog is
the supported path on mobile.

### Run the test matrix locally

```bash
# Default: tests the live GitHub Pages URL
bash scripts/test-matrix.sh

# Against a local server
python3 -m http.server 8765 --bind 127.0.0.1 >/tmp/kanban-server.log 2>&1 &
KANBAN_TEST_URL=http://127.0.0.1:8765/ bash scripts/test-matrix.sh
```

This runs:

- 6 unit tests (CLI + schema)
- 10 browser tests (page render, accessibility landmarks, button click, dialog)
- 4 static-file sanity checks

…and writes dated evidence to `kanban/tests/evidence/` plus
`kanban/tests/TEST_MATRIX.md`.

### What the matrix does NOT cover

- **Chrome / Safari engines** — only Camoufox (Firefox-based) is run.
  Code is portable; adding a Chromium step requires a Playwright runner.
- **Tablet / mobile viewports** — the Camofox HTTP API does not expose a
  viewport override endpoint in this build. `style.css` declares `@media`
  rules for `≤720px`; verifying them needs a Playwright step that resizes
  the page or a real device pass.
- **Touch input** — same constraint. The dialog form is the touch path.

## Limitations (honest)

- **No live multi-user editing.** Two people editing the same `board.json`
  at the same time will conflict. Last-write-wins on push, otherwise the
  usual git merge rules apply.
- **The browser can't commit.** Use the CLI or git directly.
- **No auth on the static site.** Don't put secrets in `board.json`.
