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
        model_dir = None
    else:
        model_dir = next((p for p in model_dirs if p.name == model_dropdown.value), None)

    if model_dir is None:
        results_json_path = None
    else:
        _results_candidates = sorted(model_dir.glob("results_*.json"))
        results_json_path = _results_candidates[-1] if _results_candidates else None
    return (results_json_path,)


@app.cell
def _(model_dirs, model_dropdown):
    if model_dropdown.value is None:
        model_dir = None
    else:
        model_dir = next((p for p in model_dirs if p.name == model_dropdown.value), None)

    if model_dir is None:
        samples_jsonl_path = None
    else:
        _samples_candidates = sorted(model_dir.glob("samples_*.jsonl"))
        samples_jsonl_path = _samples_candidates[-1] if _samples_candidates else None

    return (samples_jsonl_path,)


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
    def model_names_for_run(run_dir):
        if run_dir is None:
            return set()
        return {p.name for p in run_dir.iterdir() if p.is_dir()}

    models_a = model_names_for_run(run_dir_a)
    models_b = model_names_for_run(run_dir_b)
    common = sorted(models_a & models_b) if models_a and models_b else sorted(models_a | models_b)

    model_compare = mo.ui.dropdown(
        options=common,
        value=common[0] if common else None,
        label="Model (for comparison)",
    )
    return model_compare


@app.cell
def _(model_compare, run_dir_a, run_dir_b):
    def pick_latest(globbed):
        items = sorted(globbed)
        return items[-1] if items else None

    def paths_for(run_dir):
        if run_dir is None or model_compare.value is None:
            return None, None, None
        model_dir = run_dir / model_compare.value
        if not model_dir.exists():
            return model_dir, None, None
        results_path = pick_latest(model_dir.glob("results_*.json"))
        samples_path = pick_latest(model_dir.glob("samples_*.jsonl"))
        return model_dir, results_path, samples_path

    model_dir_a, results_path_a, samples_path_a = paths_for(run_dir_a)
    model_dir_b, results_path_b, samples_path_b = paths_for(run_dir_b)
    return model_dir_a, model_dir_b, results_path_a, results_path_b, samples_path_a, samples_path_b


@app.cell
def _(json, results_path_a, results_path_b):
    def load_json(path):
        if path is None or not path.exists():
            return None
        return json.loads(path.read_text())

    results_a = load_json(results_path_a)
    results_b = load_json(results_path_b)
    return results_a, results_b


@app.cell
def _(mo, results_a, results_b, run_a, run_b):
    def extract_headline(blob):
        if not isinstance(blob, dict):
            return None, None, None, None
        he = (blob.get("results", {}) or {}).get("humaneval", {}) or {}
        p1 = he.get("pass@1,create_test")
        p1_se = he.get("pass@1_stderr,create_test")
        cfg = blob.get("config", {}) or {}
        dtype = cfg.get("model_dtype")
        device = cfg.get("device")
        return p1, p1_se, dtype, device

    a_p1, a_se, a_dtype, a_device = extract_headline(results_a)
    b_p1, b_se, b_dtype, b_device = extract_headline(results_b)
    delta = (a_p1 - b_p1) if (a_p1 is not None and b_p1 is not None) else None

    def fmt_pct(x):
        return f"{x:.2%}" if isinstance(x, (int, float)) else "—"

    mo.md(
        "### Headline\n\n"
        f"- **Run A**: `{run_a.value}` pass@1={fmt_pct(a_p1)} (± {fmt_pct(a_se)}) dtype={a_dtype or '—'} device={a_device or '—'}\n"
        f"- **Run B**: `{run_b.value}` pass@1={fmt_pct(b_p1)} (± {fmt_pct(b_se)}) dtype={b_dtype or '—'} device={b_device or '—'}\n"
        f"- **Δ pass@1 (A−B)**: {fmt_pct(delta) if delta is not None else '—'}"
    )
    return


@app.cell
def _(mo, pl, results_a, results_b, run_a, run_b):
    # Show a small config diff table (extend as needed)
    def cfg(blob):
        if not isinstance(blob, dict):
            return {}
        return blob.get("config", {}) or {}

    keys = [
        "model_dtype",
        "device",
        "model_num_parameters",
        "model_revision",
        "random_seed",
        "torch_seed",
        "numpy_seed",
    ]
    a = cfg(results_a)
    b = cfg(results_b)
    rows = []
    for k in keys:
        rows.append({"field": k, "A": a.get(k), "B": b.get(k)})

    df = pl.DataFrame(rows)
    mo.md("### Config (selected fields)")
    mo.ui.table(df)
    return


@app.cell
def _(pl, samples_path_a, samples_path_b):
    def load_samples(path):
        if path is None or not path.exists():
            return None
        df = pl.read_ndjson(path)
        # normalize a couple convenient columns
        df = df.with_columns(
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
        return df

    samples_a = load_samples(samples_path_a)
    samples_b = load_samples(samples_path_b)
    return samples_a, samples_b


@app.cell
def _(mo, samples_a, samples_b):
    if samples_a is None or samples_b is None:
        mo.md("_No samples file(s) found for one or both runs._")
        task_options = []
    else:
        # tasks present in both
        common = sorted(set(samples_a["task_id"].to_list()) & set(samples_b["task_id"].to_list()))
        task_options = common

    task = mo.ui.dropdown(
        options=task_options,
        value=task_options[0] if task_options else None,
        label="Task (for output diff)",
    )
    return task


@app.cell
def _(difflib, mo, run_a, run_b, samples_a, samples_b, task):
    if task.value is None or samples_a is None or samples_b is None:
        return

    a_row = samples_a.filter(samples_a["task_id"] == task.value).head(1)
    b_row = samples_b.filter(samples_b["task_id"] == task.value).head(1)
    if a_row.height == 0 or b_row.height == 0:
        mo.md("_Task not found in one of the runs._")
        return

    a_prompt = a_row["prompt"][0]
    a_comp = a_row["completion"][0] or ""
    a_pass = a_row["pass@1"][0]

    b_prompt = b_row["prompt"][0]
    b_comp = b_row["completion"][0] or ""
    b_pass = b_row["pass@1"][0]

    # sanity: prompts should match; show once
    mo.md(f"### {task.value}")
    mo.md(f"- **Run A** `{run_a.value}` pass@1={a_pass}\n- **Run B** `{run_b.value}` pass@1={b_pass}")
    mo.md("#### Prompt")
    mo.md(f"```python\n{a_prompt}\n```")

    mo.md("#### Completion diff (A → B)")
    diff = "\n".join(
        difflib.unified_diff(
            a_comp.splitlines(),
            b_comp.splitlines(),
            fromfile=f"A:{run_a.value}",
            tofile=f"B:{run_b.value}",
            lineterm="",
        )
    )
    mo.md(f"```diff\n{diff if diff.strip() else '(no differences)'}\n```")
    return


if __name__ == "__main__":
    app.run()
