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
# Activate the virtual environment
source .venv/bin/activate

# Or run commands directly via uv
uv run python main.py
```

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

Generated code execution uses Docker for isolation by default.

```bash
# Build the sandbox image
docker build -t controller1-sandbox .

# View sandbox config
uv run python main.py sandbox
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
      pass@1 (n=200)
      pass@10 (n=200)
      pass@100 (n=200)

CONTROLLER:
  - Candidates: 10
  - Selection passes: 0
  - Total compute: 10 forward passes

FAIR COMPARISON:
  Controller vs pass@1 from 10 samples
============================================================
```

## Running Baselines

```bash
# Greedy baseline (pass@1, temp=0)
uv run python scripts/run_baselines.py \
    --model bigcode/starcoder2-3b \
    --benchmark humaneval \
    --mode greedy

# Sampling baseline (pass@k estimation)
uv run python scripts/run_baselines.py \
    --model bigcode/starcoder2-3b \
    --benchmark humaneval \
    --mode sampling \
    --num-samples 200 \
    --temperature 0.8
```

## Why Lock These Down?

From the research checklist:

1. **Prompt Contract**: Tiny changes to imports, typing, or wrappers can swing scores. The OpenAI repo is the canonical reference.

2. **Execution Sandbox**: Even for your own models, you're executing generated code. Docker/firejail provides isolation. Critical for self-consistency style sampling where you execute *more* code.

3. **Metrics**: Without compute budget matching, "entropic collapse helped" can quietly mean "I changed the sampling distribution." Always compare against the same compute budget.
