#!/usr/bin/env python3
"""Tests for kanban/cli.py — run with:
  python3 -m unittest discover -s kanban/tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "kanban" / "cli.py"


def run_cli(*args, stdin=None, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        input=stdin, capture_output=True, cwd=cwd,
    )


class TestKanbanCLI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmp = Path(self.tmpdir) / "board.json"
        self.original = (ROOT / "kanban" / "board.json").read_text()
        # write a minimal valid board
        self.tmp.write_text(self.original)

    def tearDown(self):
        # Restore the actual board.json (we only ever wrote via subprocess to /tmp)
        pass

    def test_validate_passes_for_seed(self):
        r = run_cli("validate")
        self.assertEqual(r.returncode, 0, r.stderr.decode())
        self.assertIn(b"valid", r.stdout)

    def test_preflight_passes_for_seed(self):
        r = run_cli("preflight")
        self.assertEqual(r.returncode, 0, r.stderr.decode())

    def test_show_emits_valid_json(self):
        r = run_cli("show")
        self.assertEqual(r.returncode, 0)
        board = json.loads(r.stdout)
        self.assertIn("cards", board)
        self.assertIn("columns", board)

    def test_required_columns_present(self):
        r = run_cli("show")
        board = json.loads(r.stdout)
        col_ids = {c["id"] for c in board["columns"]}
        self.assertEqual(col_ids, {"todo", "in_progress", "done"})

    def test_at_least_one_card_per_column(self):
        r = run_cli("show")
        board = json.loads(r.stdout)
        cols_with_cards = {c["column"] for c in board["cards"]}
        for col in ("todo", "in_progress", "done"):
            self.assertIn(col, cols_with_cards, f"no card in column {col}")

    def test_card_schema(self):
        r = run_cli("show")
        board = json.loads(r.stdout)
        for card in board["cards"]:
            self.assertIn("id", card)
            self.assertIn("title", card)
            self.assertIn("column", card)
            # Checklist items have done + text
            for sub in card.get("subtasks", []):
                self.assertIn("done", sub)
                self.assertIn("text", sub)


if __name__ == "__main__":
    unittest.main(verbosity=2)
