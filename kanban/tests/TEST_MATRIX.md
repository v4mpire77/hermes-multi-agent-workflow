# Test matrix

| | |
|---|---|
| Generated | `2026-06-02T04:43:07Z` |
| Target URL | `https://v4mpire77.github.io/hermes-multi-agent-workflow/kanban/` |
| Engine | `Camoufox (Firefox-compatible, via Camofox HTTP API)` |
| Headless | `true` |
| Camofox health | `{"ok":true,"engine":"camoufox","browserConnected":true,"browserRunning":true,"activeTabs":10,"activeSessions":6,"consecutiveFailures":0}` |

## What ran

1. **Unit tests** (`kanban/tests/test_cli.py`) — 6 tests covering schema
   validation, required columns, card schema, and the CLI's `validate`,
   `preflight`, and `show` subcommands.
2. **Browser tests** (`kanban/tests/test_browser.py`) — 10 tests driving a
   real Camoufox (Firefox-compatible) browser via the Camofox HTTP API:
   - Page URL resolved correctly
   - Document title present
   - All 3 columns render (\"To Do\", \"In Progress\", \"Done\")
   - All 3 seed cards render with the expected titles
   - \"+ Add card\" and \"Propose board.json change\" buttons present
   - Accessibility landmarks present (banner, main, three column regions)
   - Subtask checkboxes render in the accessibility tree
   - Desktop screenshot captured (file: `kanban/tests/evidence/desktop_*.png`)
   - \"+ Add card\" button click opens the dialog
   - Two independent browser sessions can coexist
3. **Static file sanity** — all 4 kanban files present (`index.html`,
   `style.css`, `app.js`, `board.json`).

## Evidence files

```
  - desktop_kanban-test-13f013c9.png
  - desktop_kanban-test-943fd078.png
  - desktop_kanban-test-e3f63f96.png
  - dialog_kanban-test-13f013c9.png
  - dialog_kanban-test-943fd078.png
  - dialog_kanban-test-e3f63f96.png
```

## Browsers / devices — honest scope

This test matrix ran against **one** engine (Camoufox, which is Firefox-based)
at **one** viewport (the daemon's default, ~1280x720). The README's
\"Browser/device testing\" section says so explicitly.

- ✅ **Firefox-compatible desktop render** — covered above
- ❌ **Chrome / Chromium** — not tested. Code uses only standards-track APIs
  (HTML5 drag/drop, ARIA landmarks, CSS media queries, no framework), so it
  should work in Chrome. Empirical pass requires running this harness with
  a Chromium-based engine.
- ❌ **Safari / WebKit** — not tested. iOS Safari does not support HTML5
  drag/drop, so the page intentionally exposes the dialog form as a
  keyboard/touch alternative (verified by reading `app.js`).
- ❌ **Tablet / mobile viewports** — Camofox does not expose a viewport
  override endpoint in this build. `style.css` declares @media rules for
  ≤720px; verifying the mobile layout requires a real device or a Playwright
  step that resizes the page.
- ❌ **Touch input** — same constraint: no touch simulation endpoint. The
  CSS handles `:hover` and `:focus` distinctly; the dialog form is the
  touch-friendly path.

## How to expand the matrix

To add Chrome and Safari coverage, swap the engine:

```bash
# Use a Playwright-managed Chromium instead
KANBAN_ENGINE=Chromium KANBAN_TEST_URL=http://127.0.0.1:8765/ python3 -m playwright install chromium
# then a Playwright harness can drive the same matrix
```

To add viewport coverage, run the harness with a Playwright launcher that
sets `viewport={'width': 375, 'height': 667}` (or 768x1024 for tablet)
before navigation, and assert that the snapshot's column regions collapse
or wrap as expected from the CSS @media rules.

