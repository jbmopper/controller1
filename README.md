# Controller1

Research project investigating controllers and decoding strategies for LLMs.

## Focus

- Controller mechanisms for language model generation
- Novel decoding strategies
- Evaluation using HumanEval and MBPP benchmarks
- Small model experiments

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Create venv (uv will use Python 3.13 per .python-version)
uv venv

# Activate the virtual environment
source .venv/bin/activate

# Or run commands directly via uv
uv run python main.py
```

### Python Environments

| Component | Python | Purpose |
|-----------|--------|---------|
| **uv venv** | 3.13.x (from `.python-version`) | Model inference, baseline runs, tests |
| **Docker sandbox** | 3.13.1 (pinned in `Dockerfile`) | Execute generated code in isolation |

Both environments use Python 3.13 for consistency. The Docker image is pinned to
`python:3.13.1-slim-bookworm` for reproducibility.

## Project Structure

```
controller1/
├── config/                 # Locked-down configurations
│   ├── prompts.py         # Exact prompt contracts (HumanEval/MBPP)
│   ├── sandbox.py         # Code execution sandbox settings
│   └── metrics.py         # Evaluation metrics and baselines
├── scripts/
│   └── run_baselines.py   # Baseline evaluation runner
├── Dockerfile             # Isolated code execution environment
├── main.py                # CLI entry point
└── pyproject.toml         # Project configuration
```

## Locked-Down Configurations

Before writing controller code, these three elements are locked down:

### 1. Prompt Contract

The exact prompt format for each benchmark. Changes here affect comparability.

```bash
uv run python main.py prompt --benchmark humaneval
uv run python main.py prompt --benchmark mbpp
```

### 2. Execution Sandbox

For controller experiments, generated code execution is intended to use Docker for isolation by default.
(The current baseline runner shells out to `lm_eval`, which uses its own execution runner.)

```bash
# Build the sandbox image
docker build -t controller1-sandbox .

# View sandbox config
uv run python main.py sandbox
```

To verify you are using the same evaluation setup across runs (and to catch
silent drift), print the contract fingerprints:

```bash
uv run python main.py contracts
```

### 3. Evaluation Metrics

Baselines and compute-matched comparisons:

```bash
uv run python main.py protocol
```

Output:
```
============================================================
EVALUATION PROTOCOL
============================================================
Benchmark: humaneval
Seed: 42

BASELINES:
  - Greedy (temp=0): pass@1
  - Sampling (temp=0.8):
      pass@1 (n=1)

CONTROLLER:
  - Candidates: 10
  - Selection passes: 0
  - Total compute: 10 forward passes

FAIR COMPARISON:
  Controller vs pass@10 sampling
============================================================
```

## Running Baselines

```bash
# Greedy baseline (pass@1, temp=0)
uv run python scripts/run_baselines.py \
    --model bigcode/starcoder2-3b \
    --benchmark humaneval \
    --mode greedy

# Sampling baseline (single run; multi-sample aggregation not implemented here yet)
uv run python scripts/run_baselines.py \
    --model bigcode/starcoder2-3b \
    --benchmark humaneval \
    --mode sampling \
    --num-samples 1 \
    --temperature 0.8
```

## Why Lock These Down?

From the research checklist:

1. **Prompt Contract**: Tiny changes to imports, typing, or wrappers can swing scores. The OpenAI repo is the canonical reference.

2. **Execution Sandbox**: Even for your own models, you're executing generated code. Docker/firejail provides isolation. Critical for self-consistency style sampling where you execute *more* code.

3. **Metrics**: Without compute budget matching, "entropic collapse helped" can quietly mean "I changed the sampling distribution." Always compare against the same compute budget.
