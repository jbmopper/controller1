"""Baseline results explorer (Marimo)."""

import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    from pathlib import Path

    import pandas as pd

    import marimo as mo
    return Path, json, mo, pd


@app.cell
def _(Path, mo):
    # Resolve results directory relative to this file
    results_root = (Path(__file__).parent.parent.parent / "results" / "baselines").resolve()

    if not results_root.exists():
        header = mo.md(
            f"❌ Results directory not found: `{results_root}`\n\n"
            "Run some baselines first."
        )
    else:
        header = mo.md(f"## Baseline Results\n\nResults root: `{results_root}`")
    return (results_root,)


@app.cell
def _(results_root):
    if not results_root.exists():
        run_dirs = []
        run_names = []
    else:
        run_dirs = sorted([p for p in results_root.iterdir() if p.is_dir()])
        run_names = [p.name for p in run_dirs]
    return run_dirs, run_names


@app.cell
def _(mo, run_names):
    run_dropdown = mo.ui.dropdown(
        options=run_names,
        value=run_names[-1] if run_names else None,
        label="Run",
    )
    return (run_dropdown,)


@app.cell
def _(run_dirs, run_dropdown):
    if run_dropdown.value is None:
        run_dir = None
    else:
        run_dir = next((p for p in run_dirs if p.name == run_dropdown.value), None)
    return (run_dir,)


@app.cell
def _(run_dir):
    if run_dir is None:
        model_dirs = []
        model_names = []
    else:
        model_dirs = sorted([p for p in run_dir.iterdir() if p.is_dir()])
        model_names = [p.name for p in model_dirs]
    return model_dirs, model_names


@app.cell
def _(mo, model_names):
    model_dropdown = mo.ui.dropdown(
        options=model_names,
        value=model_names[0] if model_names else None,
        label="Model",
    )
    return (model_dropdown,)


@app.cell
def _(mo, model_dropdown, run_dropdown):
    controls = mo.hstack([run_dropdown, model_dropdown], gap=2)
    return


@app.cell
def _(model_dirs, model_dropdown):
    if model_dropdown.value is None:
        model_dir = None
    else:
        model_dir = next((p for p in model_dirs if p.name == model_dropdown.value), None)

    if model_dir is None:
        results_json_path = None
        samples_jsonl_path = None
    else:
        _results_candidates = sorted(model_dir.glob("results_*.json"))
        _samples_candidates = sorted(model_dir.glob("samples_*.jsonl"))
        results_json_path = _results_candidates[-1] if _results_candidates else None
        samples_jsonl_path = _samples_candidates[-1] if _samples_candidates else None
    return (results_json_path,)


@app.cell
def _(json, results_json_path):
    if results_json_path is None or not results_json_path.exists():
        results_data = None
    else:
        results_data = json.loads(results_json_path.read_text())
    return (results_data,)


@app.cell
def _(mo, results_data):
    if results_data is None:
        results_view = mo.md("_No results file found._")
    else:
        _humaneval = results_data.get("results", {}).get("humaneval", {})
        _pass_at_1 = _humaneval.get("pass@1,create_test")
        _pass_at_1_stderr = _humaneval.get("pass@1_stderr,create_test")
        _model_name = results_data.get("model_name", "unknown")

        if _pass_at_1 is not None:
            _metric = f"**pass@1**: {_pass_at_1:.2%}" + (f" (± {_pass_at_1_stderr:.2%})" if _pass_at_1_stderr else "")
        else:
            _metric = "_No pass@1 metric found_"

        results_view = mo.vstack([
            mo.md(f"### {_model_name}"),
            mo.md(_metric),
            mo.md("#### Full results"),
            mo.json(results_data),
        ])
    return


@app.cell
def _(json, pd, results_root):
    # Build summary table across all runs
    if not results_root.exists():
        summary_df = pd.DataFrame()
    else:
        _rows = []
        for _rd in sorted(results_root.iterdir()):
            if not _rd.is_dir():
                continue
            for _md in sorted(_rd.iterdir()):
                if not _md.is_dir():
                    continue
                _results_files = sorted(_md.glob("results_*.json"))
                if not _results_files:
                    continue
                _rf = _results_files[-1]
                try:
                    _blob = json.loads(_rf.read_text())
                    _heval = _blob.get("results", {}).get("humaneval", {})
                    _p1 = _heval.get("pass@1,create_test")
                    _rows.append({
                        "run": _rd.name,
                        "model": _md.name,
                        "pass@1": _p1,
                    })
                except Exception:
                    continue

        summary_df = pd.DataFrame(_rows)
    return (summary_df,)


@app.cell
def _(mo, summary_df):
    if summary_df.empty:
        summary_view = mo.md("_No results found._")
    else:
        summary_view = mo.vstack([
            mo.md("### Summary (all runs)"),
            mo.ui.table(summary_df),
        ])
    return


if __name__ == "__main__":
    app.run()
