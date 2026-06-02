# Kanban tests

This directory contains two test suites plus the evidence captured from
the most recent run.

## Suites

### `test_cli.py` — unit tests (no browser needed)

Six tests covering the CLI's `validate`, `preflight`, and `show`
subcommands, the JSON schema (required columns, card schema), and the
presence of at least one card in each column.

```bash
python3 -m unittest discover -s kanban/tests -p 'test_cli.py' -v
```

Runs in well under a second. Safe to run in any environment that has
Python 3 and the standard library.

### `test_browser.py` — real-browser tests (Camoufox required)

Ten tests driving a real Firefox-compatible browser engine (Camoufox)
via the Camofox HTTP API. The page is loaded from
`https://v4mpire77.github.io/hermes-multi-agent-workflow/kanban/` by
default; override with `KANBAN_TEST_URL=...`.

The tests verify:

1. Page URL resolved correctly
2. Document title present
3. All 3 columns render
4. All 3 seed cards render with the expected titles
5. "+ Add card" and "Propose board.json change" buttons present
6. Accessibility landmarks present (banner, main, three column regions)
7. Subtask checkboxes render in the accessibility tree
8. Desktop screenshot captured (file: `evidence/desktop_*.png`)
9. "+ Add card" button click opens the dialog
10. Two independent browser sessions can coexist

```bash
python3 -m kanban.tests.test_browser -v
```

Takes about 15-20 seconds. Requires:

- `CAMOFOX_URL` reachable (default: `http://camofox:9377`)
- The daemon's `browserRunning` flag set to `true` (check `/health`)

### `test-matrix.sh` — orchestrator script

Runs both suites plus a static-file sanity check, then writes the
dated evidence report to `TEST_MATRIX.md` and the screenshots to
`evidence/`.

```bash
bash scripts/test-matrix.sh
```

Override the target URL with `KANBAN_TEST_URL=http://127.0.0.1:8765/`
to test a local server instead of GitHub Pages.

## Evidence

After a run, `evidence/` contains dated PNGs of the rendered board and
the open dialog. The exact files vary per run (random user/session IDs),
but the count and naming pattern are stable:

```
evidence/desktop_<random>.png     # full board, light or dark
evidence/dialog_<random>.png      # board with edit dialog open
```

`TEST_MATRIX.md` is a Markdown report describing the run: timestamp,
target URL, engine, what passed, what evidence was captured, and the
honest scope (what was NOT tested and why).

## Honest limitations

- The browser test suite runs against **one engine** (Camoufox).
  Chrome and Safari are not directly tested.
- The browser test suite runs at **one viewport** (the daemon's default,
  ~1280x720). Tablet and mobile viewports are not tested.
- The harness does not check the JS console for errors. The Camofox
  HTTP API in this build does not expose a `/console` endpoint; if you
  need console-error capture, swap in Playwright with `page.on('console')`.
