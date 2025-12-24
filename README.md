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

## Evaluation

This project uses the [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) for benchmarking.

```bash
# Example: Run HumanEval
uv run lm_eval --model hf --model_args pretrained=<model_name> --tasks humaneval

# Example: Run MBPP
uv run lm_eval --model hf --model_args pretrained=<model_name> --tasks mbpp
```

## Project Structure

```
controller1/
├── main.py           # Entry point
├── pyproject.toml    # Project configuration
├── uv.lock           # Locked dependencies
└── README.md         # This file
```

