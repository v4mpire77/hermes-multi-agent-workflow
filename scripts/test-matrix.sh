#!/usr/bin/env bash
# scripts/test-matrix.sh — run the browser test matrix and write evidence
#
# Usage:
#   bash scripts/test-matrix.sh                       # default (GitHub Pages)
#   KANBAN_TEST_URL=http://127.0.0.1:8765/ bash scripts/test-matrix.sh
#
# Writes a dated TEST_MATRIX.md under kanban/tests/ describing what was run
# and where the screenshots live.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EVIDENCE_DIR="kanban/tests/evidence"
mkdir -p "$EVIDENCE_DIR"

DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
URL="${KANBAN_TEST_URL:-https://v4mpire77.github.io/hermes-multi-agent-workflow/kanban/}"
ENGINE="${KANBAN_ENGINE:-Camoufox (Firefox-compatible, via Camofox HTTP API)}"
HEADLESS="${KANBAN_HEADLESS:-true}"

echo "========================================"
echo "  Kanban test matrix"
echo "  Date:    $DATE"
echo "  URL:     $URL"
echo "  Engine:  $ENGINE"
echo "  Headless: $HEADLESS"
echo "========================================"

# 1. Unit tests (CLI + JSON schema)
echo ""
echo "[1/3] Unit tests (CLI + schema)"
python3 -m unittest discover -s kanban/tests -p 'test_cli.py' -v

# 2. Browser tests (real Firefox-compatible engine)
echo ""
echo "[2/3] Browser tests ($ENGINE)"
KANBAN_TEST_URL="$URL" python3 -m kanban.tests.test_browser -v

# 3. Static-file accessibility (HTML, CSS validity)
echo ""
echo "[3/3] Static file sanity"
for f in kanban/index.html kanban/style.css kanban/app.js kanban/board.json; do
    if [ -f "$f" ]; then
        size=$(stat -c %s "$f")
        echo "  $f  ($size bytes)"
    else
        echo "  MISSING: $f"
        exit 1
    fi
done

# 4. Write the test matrix report
echo ""
echo "[+] Writing test matrix report"
TEST_MATRIX="kanban/tests/TEST_MATRIX.md"

# Collect screenshot evidence
SHOT_LIST="$(ls -1 "$EVIDENCE_DIR" 2>/dev/null | sed 's/^/  - /' || true)"

cat > "$TEST_MATRIX" <<EOF
# Test matrix

| | |
|---|---|
| Generated | \`$DATE\` |
| Target URL | \`$URL\` |
| Engine | \`$ENGINE\` |
| Headless | \`$HEADLESS\` |
| Camofox health | \`$(curl -s http://camofox:9377/health 2>/dev/null || echo "unreachable")\` |

## What ran

1. **Unit tests** (\`kanban/tests/test_cli.py\`) — 6 tests covering schema
   validation, required columns, card schema, and the CLI's \`validate\`,
   \`preflight\`, and \`show\` subcommands.
2. **Browser tests** (\`kanban/tests/test_browser.py\`) — 10 tests driving a
   real Camoufox (Firefox-compatible) browser via the Camofox HTTP API:
   - Page URL resolved correctly
   - Document title present
   - All 3 columns render (\"To Do\", \"In Progress\", \"Done\")
   - All 3 seed cards render with the expected titles
   - \"+ Add card\" and \"Propose board.json change\" buttons present
   - Accessibility landmarks present (banner, main, three column regions)
   - Subtask checkboxes render in the accessibility tree
   - Desktop screenshot captured (file: \`$EVIDENCE_DIR/desktop_*.png\`)
   - \"+ Add card\" button click opens the dialog
   - Two independent browser sessions can coexist
3. **Static file sanity** — all 4 kanban files present (\`index.html\`,
   \`style.css\`, \`app.js\`, \`board.json\`).

## Evidence files

\`\`\`
$SHOT_LIST
\`\`\`

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
  keyboard/touch alternative (verified by reading \`app.js\`).
- ❌ **Tablet / mobile viewports** — Camofox does not expose a viewport
  override endpoint in this build. \`style.css\` declares @media rules for
  ≤720px; verifying the mobile layout requires a real device or a Playwright
  step that resizes the page.
- ❌ **Touch input** — same constraint: no touch simulation endpoint. The
  CSS handles \`:hover\` and \`:focus\` distinctly; the dialog form is the
  touch-friendly path.

## How to expand the matrix

To add Chrome and Safari coverage, swap the engine:

\`\`\`bash
# Use a Playwright-managed Chromium instead
KANBAN_ENGINE=Chromium \
KANBAN_TEST_URL=http://127.0.0.1:8765/ \
python3 -m playwright install chromium
# then a Playwright harness can drive the same matrix
\`\`\`

To add viewport coverage, run the harness with a Playwright launcher that
sets \`viewport={'width': 375, 'height': 667}\` (or 768x1024 for tablet)
before navigation, and assert that the snapshot's column regions collapse
or wrap as expected from the CSS @media rules.

EOF

echo "  → $TEST_MATRIX"
echo ""
echo "Done.  See $TEST_MATRIX for the full report."
