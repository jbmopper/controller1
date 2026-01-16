import json
from pathlib import Path

import marimo as mo

__generated_with = "0.19.4"
app = mo.App(width="medium")


@app.cell
def _():
    # Repo-relative: controller1/analysis -> controller1/results
    results_root = (Path("..") / "results" / "baselines").resolve()
    mo.md(f"## Controller1 baselines\n\nResults root: `{results_root}`")
    return results_root,


@app.cell
def _(results_root):
    if not results_root.exists():
        mo.md("**No results directory found.** Run baselines first.")
        run_dirs: list[Path] = []
        run_names: list[str] = []
    else:
        run_dirs = sorted([p for p in results_root.iterdir() if p.is_dir()])
        run_names = [p.name for p in run_dirs]
    return run_dirs, run_names


@app.cell
def _(run_names):
    mo.md("### Pick a run")
    run = mo.ui.dropdown(
        options=run_names,
        value=run_names[-1] if run_names else None,
        label="Run directory",
    )
    run
    return run,


@app.cell
def _(run, run_dirs):
    if run.value is None:
        mo.md("_No runs found yet._")
        metadata_path = None
    else:
        run_dir = next((p for p in run_dirs if p.name == run.value), None)
        metadata_path = run_dir / "run_metadata.json" if run_dir else None
    return metadata_path,


@app.cell
def _(metadata_path):
    if metadata_path is None or not metadata_path.exists():
        mo.md("No `run_metadata.json` found for this run.")
        metadata = None
    else:
        metadata = json.loads(metadata_path.read_text())
        mo.md("### run_metadata.json")
        mo.json(metadata)
    return metadata,


if __name__ == "__main__":
    app.run()