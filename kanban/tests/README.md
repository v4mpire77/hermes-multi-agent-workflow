# Test fixtures for the kanban board.

This directory is reserved for unit tests of the kanban CLI and the
integration with `engine/kanban_store.py`.

Quick smoke test (manual):

```
python3 kanban/cli.py validate
python3 kanban/cli.py preflight
```

Automated tests live here once added; the upstream template ships a
`tests/` for the engine — the kanban tests should follow the same
naming and discovery pattern.
