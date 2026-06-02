#!/usr/bin/env python3
"""Browser-driven tests for the static Kanban viewer.

Drives a real browser engine (Camoufox — Firefox-compatible) via the Camofox
HTTP API to verify the live page renders, the seed cards appear, and the
"+ Add card" dialog opens.  Snapshots + screenshots are captured for each
viewport / session key as evidence in ``TEST_MATRIX.md``.

This is *not* a synthetic DOM test — it loads the actual published page from
GitHub Pages (or ``localhost:PORT`` if you set ``KANBAN_TEST_URL``).

Run::

    python3 -m kanban.tests.test_browser            # default URL (pages)
    KANBAN_TEST_URL=http://127.0.0.1:8765/ python3 -m kanban.tests.test_browser
    KANBAN_TEST_URL=... python3 -m unittest kanban.tests.test_browser -v

The harness exits non-zero on any failure, so it is CI-friendly.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import unittest
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import request as urlrequest
from urllib.error import URLError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CAMOFOX_URL = os.environ.get("CAMOFOX_URL", "http://camofox:9377").rstrip("/")
TEST_URL = os.environ.get(
    "KANBAN_TEST_URL",
    "https://v4mpire77.github.io/hermes-multi-agent-workflow/kanban/",
)
EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"

# Reasonable default desktop viewport.  Camofox does not expose a viewport
# override endpoint, so we run all tests at whatever the daemon's default is.
DEFAULT_USER = f"kanban-test-{uuid.uuid4().hex[:8]}"
DEFAULT_SESSION = f"session-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Camofox HTTP client (minimal, only what we need)
# ---------------------------------------------------------------------------

class CamofoxError(RuntimeError):
    """Raised when the Camofox HTTP API returns an error or is unreachable."""


def _http(method: str, path: str, body: Optional[dict] = None,
          timeout: float = 30) -> Tuple[int, Any]:
    url = f"{CAMOFOX_URL}{path}"
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urlrequest.Request(url, data=data, headers=headers, method=method)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = resp.status
    except URLError as e:
        raise CamofoxError(f"{method} {path}: {e}") from e
    # Try JSON, fall back to raw text
    try:
        return status, json.loads(raw.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return status, raw


def _health() -> Dict[str, Any]:
    _, data = _http("GET", "/health")
    return data  # type: ignore[return-value]


def _create_tab(user: str, session: str) -> str:
    """Create a blank tab and return its tabId."""
    status, data = _http("POST", "/tabs", {"userId": user, "sessionKey": session})
    if status != 200 or "tabId" not in data:
        raise CamofoxError(f"create_tab failed: {status} {data}")
    return data["tabId"]


def _navigate(tab_id: str, user: str, url: str) -> Dict[str, Any]:
    status, data = _http(
        "POST", f"/tabs/{tab_id}/navigate",
        {"userId": user, "url": url},
        timeout=60,
    )
    if status != 200 or data.get("ok") is not True:
        raise CamofoxError(f"navigate failed: {status} {data}")
    return data  # type: ignore[return-value]


def _snapshot_raw(tab_id: str, user: str) -> Dict[str, Any]:
    url = f"{CAMOFOX_URL}/tabs/{tab_id}/snapshot?userId={user}"
    req = urlrequest.Request(url, method="GET")
    with urlrequest.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _click(tab_id: str, user: str, ref: str) -> Dict[str, Any]:
    status, data = _http(
        "POST", f"/tabs/{tab_id}/click",
        {"userId": user, "ref": ref},
    )
    return data  # type: ignore[return-value]


def _screenshot_path(tab_id: str, user: str, path: Path) -> None:
    """Save a PNG screenshot of the tab to *path*."""
    url = f"{CAMOFOX_URL}/tabs/{tab_id}/screenshot?userId={user}"
    req = urlrequest.Request(url, method="GET")
    with urlrequest.urlopen(req, timeout=30) as resp:
        path.write_bytes(resp.read())


# ---------------------------------------------------------------------------
# Test fixture
# ---------------------------------------------------------------------------

class BrowserTestCase(unittest.TestCase):
    """Base case that sets up a fresh Camofox tab and navigates to the page."""

    user: str = DEFAULT_USER
    session: str = DEFAULT_SESSION
    tab_id: str = ""
    snapshot: Dict[str, Any] = {}
    snapshot_text: str = ""

    @classmethod
    def setUpClass(cls) -> None:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        # Confirm Camofox is reachable
        h = _health()
        if not h.get("ok") or not h.get("browserRunning"):
            raise unittest.SkipTest(
                f"Camofox not healthy at {CAMOFOX_URL}: {h}",
            )
        # Create tab and navigate
        cls.tab_id = _create_tab(cls.user, cls.session)
        _navigate(cls.tab_id, cls.user, TEST_URL)
        # Allow the page's app.js to finish loading + rendering
        time.sleep(2.0)
        cls.snapshot = _snapshot_raw(cls.tab_id, cls.user)
        cls.snapshot_text = cls.snapshot.get("snapshot", "")

    @classmethod
    def tearDownClass(cls) -> None:
        # No explicit close endpoint; the tab will be GC'd by the daemon.
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBoardRenders(BrowserTestCase):
    """Verify the page loads, the seed content appears, and the
    accessibility tree is structurally valid (landmarks, headings, lists)."""

    def test_page_url(self) -> None:
        self.assertEqual(self.snapshot.get("url", "").rstrip("/"), TEST_URL.rstrip("/"))

    def test_title(self) -> None:
        self.assertIn("Kanban Board", self.snapshot_text)

    def test_three_columns_present(self) -> None:
        for col in ("To Do", "In Progress", "Done"):
            with self.subTest(column=col):
                self.assertIn(col, self.snapshot_text,
                              f"column '{col}' missing from accessibility tree")

    def test_seed_cards_present(self) -> None:
        for title in (
            "Wire scout intake → board",
            "Build research-lane fan-out",
            "Initial board seed",
        ):
            with self.subTest(card=title):
                self.assertIn(title, self.snapshot_text,
                              f"card '{title}' missing from accessibility tree")

    def test_add_card_button(self) -> None:
        self.assertIn("+ Add card", self.snapshot_text)
        self.assertIn("Propose board.json change", self.snapshot_text)

    def test_accessibility_landmarks(self) -> None:
        # banner, main, contentinfo, navigation region — all should be present
        for landmark in ("banner:", "main", 'region "To Do"',
                         'region "In Progress"', 'region "Done"'):
            with self.subTest(landmark=landmark):
                self.assertIn(landmark, self.snapshot_text,
                              f"accessibility landmark '{landmark}' missing")

    def test_card_subtasks_rendered(self) -> None:
        # At least one subtask checkbox should be visible
        self.assertIn("☐", self.snapshot_text,
                      "no unchecked subtask markers in accessibility tree")

    def test_screenshot_captured(self) -> None:
        path = EVIDENCE_DIR / f"desktop_{self.user}.png"
        _screenshot_path(self.tab_id, self.user, path)
        self.assertGreater(path.stat().st_size, 1000,
                           f"screenshot {path} is too small to be a real PNG")


class TestAddCardDialog(BrowserTestCase):
    """Verify the '+ Add card' button opens the dialog form."""

    def test_button_click_opens_dialog(self) -> None:
        # Find the ref of the + Add card button
        import re
        m = re.search(r'button "\+ Add card" \[(e\d+)\]', self.snapshot_text)
        self.assertIsNotNone(m, "+ Add card button ref not found")
        ref = m.group(1)  # type: ignore[union-attr]
        _click(self.tab_id, self.user, ref)
        time.sleep(0.5)
        snap2 = _snapshot_raw(self.tab_id, self.user)
        text = snap2.get("snapshot", "")
        # Dialog should expose a Title input and a Save button
        self.assertIn("Title", text)
        self.assertIn("Save", text)
        # Capture evidence
        path = EVIDENCE_DIR / f"dialog_{self.user}.png"
        _screenshot_path(self.tab_id, self.user, path)
        self.assertGreater(path.stat().st_size, 1000)


class TestMultipleSessions(BrowserTestCase):
    """Verify the server can host several independent sessions in parallel."""

    def test_independent_sessions(self) -> None:
        seen = set()
        for i in range(2):
            u = f"kanban-test-{uuid.uuid4().hex[:8]}"
            s = f"session-{uuid.uuid4().hex[:8]}"
            tab = _create_tab(u, s)
            _navigate(tab, u, TEST_URL)
            time.sleep(1.5)
            snap = _snapshot_raw(tab, u)
            self.assertIn("Wire scout intake → board", snap.get("snapshot", ""))
            seen.add(tab)
        self.assertEqual(len(seen), 2)


# ---------------------------------------------------------------------------
# Manual entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Print config so the test matrix has context.
    print(f"CAMOFOX_URL: {CAMOFOX_URL}", file=sys.stderr)
    print(f"TEST_URL:    {TEST_URL}", file=sys.stderr)
    print(f"EVIDENCE:    {EVIDENCE_DIR}", file=sys.stderr)
    h = _health()
    print(f"HEALTH:      {h}", file=sys.stderr)
    unittest.main(verbosity=2)
