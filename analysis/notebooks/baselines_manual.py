"""Baseline results explorer (Marimo)."""

import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Notebook for analysis of baseline data (human version)

    This notebook should have mostly human-written analysis with less of the AI's "improvements", but will use some of the code there as a model.
    """)
    return


@app.cell
def _():
    import json
    from pathlib import Path

    import plotly.graph_objects as go
    import polars as pl
    import difflib

    import marimo as mo
    return Path, mo


@app.cell
def _(Path):
    source_dir = Path("../results/baselines/")
    run_dirs = sorted([p for p in source_dir.iterdir() if p.is_dir()])
    run_names = [p.name for p in run_dirs]
    print(run_names)
    return


if __name__ == "__main__":
    app.run()
