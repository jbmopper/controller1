## Analysis subproject

This directory is a **separate Python project** (managed with `uv`) for analysis
and writeups. It intentionally keeps notebook/plotting dependencies out of the
main `controller1` environment.

### Setup

```bash
cd analysis
uv venv
uv sync
```

### Run Marimo

```bash
cd analysis
uv run marimo edit notebooks/baselines.py
```

### Data location

Results live in `../results/` relative to this directory.

