"""Baseline results explorer (Marimo)."""

import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    from pathlib import Path

    import plotly.graph_objects as go
    import polars as pl
    import difflib

    import marimo as mo
    return Path, difflib, go, json, mo, pl


@app.cell
def _(mo):
    mo.md("""
    # Baseline Results Explorer

    This notebook lets you browse HumanEval baseline results from `controller1`.

    **Structure:**
    - Pick a **run** (e.g., `greedy_20260113_230732`) and **model** to view detailed results
    - The **summary table** at the bottom shows pass@1 across all runs/models

    Results are loaded from `../results/baselines/` relative to this notebook.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Setup

    Locate the results directory.
    """)
    return


@app.cell
def _(Path):
    # Resolve results directory relative to this file
    results_root = (Path(__file__).parent.parent.parent / "results" / "baselines").resolve()
    return (results_root,)


@app.cell
def _(mo, results_root):
    if not results_root.exists():
        mo.md(
            f"❌ Results directory not found: `{results_root}`\n\n"
            "Run some baselines first."
        )
    else:
        mo.md(f"✅ Results root: `{results_root}`")
    return


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
def _(mo):
    mo.md("""
    ---
    ## Run & Model Selection

    Choose a run and model to inspect.
    """)
    return


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
    mo.hstack([run_dropdown, model_dropdown], gap=2)
    return


@app.cell
def _(model_dirs, model_dropdown):
    if model_dropdown.value is None:
        _model_dir = None
    else:
        _model_dir = next((p for p in model_dirs if p.name == model_dropdown.value), None)

    if _model_dir is None:
        results_json_path = None
        samples_jsonl_path = None
    else:
        _results_candidates = sorted(_model_dir.glob("results_*.json"))
        _samples_candidates = sorted(_model_dir.glob("samples_*.jsonl"))
        results_json_path = _results_candidates[-1] if _results_candidates else None
        samples_jsonl_path = _samples_candidates[-1] if _samples_candidates else None

    return results_json_path, samples_jsonl_path


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Selected Run Details

    Shows pass@1 metric and full JSON for the selected run/model.
    """)
    return


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
        mo.md("_No results file found._")
    else:
        _humaneval = results_data.get("results", {}).get("humaneval", {})
        _pass_at_1 = _humaneval.get("pass@1,create_test")
        _pass_at_1_stderr = _humaneval.get("pass@1_stderr,create_test")
        _model_name = results_data.get("model_name", "unknown")

        if _pass_at_1 is not None:
            _metric = f"**pass@1**: {_pass_at_1:.2%}" + (f" (± {_pass_at_1_stderr:.2%})" if _pass_at_1_stderr else "")
        else:
            _metric = "_No pass@1 metric found_"

        mo.vstack([
            mo.md(f"### {_model_name}"),
            mo.md(_metric),
            mo.md("#### Full results"),
            mo.json(results_data),
        ])
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Summary Table

    Aggregates pass@1 across all runs and models.
    """)
    return


@app.cell
def _(json, pl, results_root):
    # Build summary table across all runs
    if not results_root.exists():
        summary_df = pl.DataFrame()
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

        summary_df = pl.DataFrame(_rows)
    return (summary_df,)


@app.cell
def _(mo, summary_df):
    if summary_df.is_empty():
        mo.md("_No results found._")
    else:
        mo.ui.table(summary_df)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Chart

    Visualize pass@1 across runs.
    """)
    return


@app.cell
def _(go, mo, pl, summary_df):
    if summary_df.is_empty():
        mo.md("_No data to plot._")
    else:
        _fig = go.Figure()
        for _model in summary_df["model"].unique().to_list():
            _subset = summary_df.filter(pl.col("model") == _model)
            _fig.add_trace(go.Bar(
                x=_subset["run"].to_list(),
                y=_subset["pass@1"].to_list(),
                name=_model,
            ))
        _fig.update_layout(
            barmode="group",
            title="pass@1 by Run and Model",
            xaxis_title="Run",
            yaxis_title="pass@1",
            yaxis_tickformat=".0%",
        )
        mo.ui.plotly(_fig)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Compare two runs

    Pick two runs (e.g., M4 fp16 vs 4090 fp32) and compare:
    - headline `pass@1`
    - key config fields (dtype/device/etc.)
    - per-problem outputs (from `samples_*.jsonl`)
    """)
    return


@app.cell
def _(mo, run_names):
    # Defaults: newest as A, previous as B (if available)
    default_a = run_names[-1] if run_names else None
    default_b = run_names[-2] if len(run_names) >= 2 else None

    run_a = mo.ui.dropdown(options=run_names, value=default_a, label="Run A")
    run_b = mo.ui.dropdown(options=run_names, value=default_b, label="Run B")
    mo.hstack([run_a, run_b], gap=2)
    return run_a, run_b


@app.cell
def _(run_a, run_b, run_dirs):
    run_dir_a = next((p for p in run_dirs if p.name == run_a.value), None) if run_a.value else None
    run_dir_b = next((p for p in run_dirs if p.name == run_b.value), None) if run_b.value else None
    return run_dir_a, run_dir_b


@app.cell
def _(mo, run_dir_a, run_dir_b):
    def _model_names_for_run(run_dir):
        if run_dir is None:
            return set()
        return {p.name for p in run_dir.iterdir() if p.is_dir()}

    _models_a = _model_names_for_run(run_dir_a)
    _models_b = _model_names_for_run(run_dir_b)
    _common = sorted(_models_a & _models_b) if _models_a and _models_b else sorted(_models_a | _models_b)

    model_compare = mo.ui.dropdown(
        options=_common,
        value=_common[0] if _common else None,
        label="Model (for comparison)",
    )
    return (model_compare,)


@app.cell
def _(model_compare, run_dir_a, run_dir_b):
    def _pick_latest(globbed):
        _items = sorted(globbed)
        return _items[-1] if _items else None

    def _paths_for(run_dir):
        if run_dir is None or model_compare.value is None:
            return None, None, None
        _model_dir = run_dir / model_compare.value
        if not _model_dir.exists():
            return _model_dir, None, None
        _results_path = _pick_latest(_model_dir.glob("results_*.json"))
        _samples_path = _pick_latest(_model_dir.glob("samples_*.jsonl"))
        return _model_dir, _results_path, _samples_path

    model_dir_a, results_path_a, samples_path_a = _paths_for(run_dir_a)
    model_dir_b, results_path_b, samples_path_b = _paths_for(run_dir_b)
    return model_dir_a, model_dir_b, results_path_a, results_path_b, samples_path_a, samples_path_b


@app.cell
def _(json, results_path_a, results_path_b):
    def _load_json(path):
        if path is None or not path.exists():
            return None
        return json.loads(path.read_text())

    results_a = _load_json(results_path_a)
    results_b = _load_json(results_path_b)
    return results_a, results_b


@app.cell
def _(mo, results_a, results_b, run_a, run_b):
    def _extract_headline(blob):
        if not isinstance(blob, dict):
            return None, None, None, None
        _he = (blob.get("results", {}) or {}).get("humaneval", {}) or {}
        _p1 = _he.get("pass@1,create_test")
        _p1_se = _he.get("pass@1_stderr,create_test")
        _cfg = blob.get("config", {}) or {}
        _dtype = _cfg.get("model_dtype")
        _device = _cfg.get("device")
        return _p1, _p1_se, _dtype, _device

    _a_p1, _a_se, _a_dtype, _a_device = _extract_headline(results_a)
    _b_p1, _b_se, _b_dtype, _b_device = _extract_headline(results_b)
    _delta = (_a_p1 - _b_p1) if (_a_p1 is not None and _b_p1 is not None) else None

    def _fmt_pct(x):
        return f"{x:.2%}" if isinstance(x, (int, float)) else "—"

    mo.md(
        "### Headline\n\n"
        f"- **Run A**: `{run_a.value}` pass@1={_fmt_pct(_a_p1)} (± {_fmt_pct(_a_se)}) dtype={_a_dtype or '—'} device={_a_device or '—'}\n"
        f"- **Run B**: `{run_b.value}` pass@1={_fmt_pct(_b_p1)} (± {_fmt_pct(_b_se)}) dtype={_b_dtype or '—'} device={_b_device or '—'}\n"
        f"- **Δ pass@1 (A−B)**: {_fmt_pct(_delta) if _delta is not None else '—'}"
    )
    return


@app.cell
def _(mo, pl, results_a, results_b):
    # Show a small config diff table (extend as needed)
    def _cfg(blob):
        if not isinstance(blob, dict):
            return {}
        return blob.get("config", {}) or {}

    _keys = [
        "model_dtype",
        "device",
        "model_num_parameters",
        "model_revision",
        "random_seed",
        "torch_seed",
        "numpy_seed",
    ]
    _a = _cfg(results_a)
    _b = _cfg(results_b)
    _rows = []
    for _k in _keys:
        _rows.append({"field": _k, "A": _a.get(_k), "B": _b.get(_k)})

    _df = pl.DataFrame(_rows)
    mo.vstack([
        mo.md("### Config (selected fields)"),
        mo.ui.table(_df),
    ])
    return


@app.cell
def _(pl, samples_path_a, samples_path_b):
    def _load_samples(path):
        if path is None or not path.exists():
            return None
        _df = pl.read_ndjson(path)
        # normalize a couple convenient columns
        _df = _df.with_columns(
            pl.col("doc").struct.field("task_id").alias("task_id"),
            pl.col("doc").struct.field("prompt").alias("prompt"),
            pl.col("filtered_resps").list.get(0).list.get(0).alias("completion"),
        ).select(
            "doc_id",
            "task_id",
            "pass@1",
            "prompt",
            "completion",
        )
        return _df

    samples_a = _load_samples(samples_path_a)
    samples_b = _load_samples(samples_path_b)
    return samples_a, samples_b


@app.cell
def _(mo, samples_a, samples_b):
    if samples_a is None or samples_b is None:
        _task_options = []
    else:
        # tasks present in both
        _task_options = sorted(set(samples_a["task_id"].to_list()) & set(samples_b["task_id"].to_list()))

    task = mo.ui.dropdown(
        options=_task_options,
        value=_task_options[0] if _task_options else None,
        label="Task (for output diff)",
    )
    return (task,)


@app.cell
def _(difflib, mo, run_a, run_b, samples_a, samples_b, task):
    if task.value is None or samples_a is None or samples_b is None:
        mo.md("_Select a task to compare._")
    else:
        _a_row = samples_a.filter(samples_a["task_id"] == task.value).head(1)
        _b_row = samples_b.filter(samples_b["task_id"] == task.value).head(1)

        if _a_row.height == 0 or _b_row.height == 0:
            mo.md("_Task not found in one of the runs._")
        else:
            _a_prompt = _a_row["prompt"][0]
            _a_comp = _a_row["completion"][0] or ""
            _a_pass = _a_row["pass@1"][0]

            _b_comp = _b_row["completion"][0] or ""
            _b_pass = _b_row["pass@1"][0]

            _diff = "\n".join(
                difflib.unified_diff(
                    _a_comp.splitlines(),
                    _b_comp.splitlines(),
                    fromfile=f"A:{run_a.value}",
                    tofile=f"B:{run_b.value}",
                    lineterm="",
                )
            )

            mo.vstack([
                mo.md(f"### {task.value}"),
                mo.md(f"- **Run A** `{run_a.value}` pass@1={_a_pass}\n- **Run B** `{run_b.value}` pass@1={_b_pass}"),
                mo.md("#### Prompt"),
                mo.md(f"```python\n{_a_prompt}\n```"),
                mo.md("#### Completion diff (A → B)"),
                mo.md(f"```diff\n{_diff if _diff.strip() else '(no differences)'}\n```"),
            ])
    return


if __name__ == "__main__":
    app.run()
