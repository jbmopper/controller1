#!/usr/bin/env python3
"""
Run baseline evaluations for HumanEval and MBPP.

This script establishes the baselines needed before any controller experiments:
1. Greedy pass@1 (temp=0) - deterministic baseline
2. Sampling pass@1 (single run) - stochastic baseline for comparison

Usage:
    # Run greedy baseline on HumanEval with a specific model
    uv run python scripts/run_baselines.py --model <model_name> --benchmark humaneval --mode greedy
    
    # Run sampling baseline (single run; repeated runs/aggregation not implemented here yet)
    uv run python scripts/run_baselines.py --model <model_name> --benchmark humaneval --mode sampling
    
    # Run both baselines
    uv run python scripts/run_baselines.py --model <model_name> --benchmark humaneval --mode all
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config.contracts import contract_report

# Enable HuggingFace code evaluation
# lm_eval uses HF's code_eval metric which requires this acknowledgment
# See: https://arxiv.org/abs/2107.03374 for sandboxing discussion
os.environ["HF_ALLOW_CODE_EVAL"] = "1"


def get_device() -> str:
    """Detect the best available device: CUDA > MPS > CPU."""
    import torch
    
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


def get_lm_eval_command(
    model: str,
    benchmark: str,
    output_dir: Path,
    mode: str = "greedy",
    num_samples: int = 1,
    temperature: float = 0.0,
) -> list[str]:
    """Build the lm_eval command for a baseline run."""
    
    device = get_device()
    print(f"Using device: {device}")
    
    # Base command
    cmd = [
        "uv", "run", "lm_eval",
        "--model", "hf",
        "--model_args", f"pretrained={model},dtype=float32",
        "--device", device,
        "--tasks", benchmark,
        "--output_path", str(output_dir),
        "--log_samples",
        "--confirm_run_unsafe_code",  # HumanEval/MBPP execute generated code
    ]
    
    # Generation kwargs based on mode
    if mode == "greedy":
        cmd.extend([
            "--gen_kwargs", "do_sample=False",
        ])
    else:
        cmd.extend([
            "--gen_kwargs", f"do_sample=True,temperature={temperature}",
            "--num_fewshot", "0",  # For HumanEval
        ])
    
    # For sampling, we need multiple repeats
    if num_samples > 1:
        # Note: lm-eval uses 'repeats' for multiple samples
        # This is set in the task config, we may need to override
        pass
    
    return cmd


def run_greedy_baseline(model: str, benchmark: str, output_dir: Path) -> dict:
    """Run greedy (deterministic) baseline."""
    print(f"\n{'='*60}")
    print(f"Running GREEDY baseline: {model} on {benchmark}")
    print(f"{'='*60}\n")
    
    run_dir = output_dir / f"greedy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = get_lm_eval_command(model, benchmark, run_dir, mode="greedy")
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    run_info = {
        "mode": "greedy",
        "model": model,
        "benchmark": benchmark,
        "output_dir": str(run_dir),
        "exit_code": result.returncode,
        "timestamp": datetime.now().isoformat(),
        "contracts": contract_report(),
    }
    
    # Save metadata to run directory
    metadata_file = run_dir / "run_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(run_info, f, indent=2)
    print(f"Metadata saved to: {metadata_file}")
    
    return run_info


def run_sampling_baseline(
    model: str, 
    benchmark: str, 
    output_dir: Path,
    num_samples: int = 200,
    temperature: float = 0.8,
) -> dict:
    """Run a single sampling baseline run (pass@1 under a non-zero temperature)."""
    print(f"\n{'='*60}")
    print(f"Running SAMPLING baseline: {model} on {benchmark}")
    print(f"  Temperature: {temperature}")
    print(f"  Num samples: {num_samples}")
    print(f"{'='*60}\n")
    
    run_dir = output_dir / f"sampling_n{num_samples}_t{temperature}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    if num_samples != 1:
        print("NOTE: This runner currently executes a single lm-eval run.")
        print("Multi-sample aggregation (pass@k / pass@N) is not implemented here yet.")
        print("Proceeding with a single run (equivalent to pass@1 under sampling).")
        print()
    
    cmd = get_lm_eval_command(
        model, benchmark, run_dir, 
        mode="sampling", 
        temperature=temperature
    )
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    run_info = {
        "mode": "sampling",
        "model": model,
        "benchmark": benchmark,
        "temperature": temperature,
        "num_samples": num_samples,
        "output_dir": str(run_dir),
        "exit_code": result.returncode,
        "timestamp": datetime.now().isoformat(),
        "contracts": contract_report(),
    }
    
    # Save metadata to run directory
    metadata_file = run_dir / "run_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(run_info, f, indent=2)
    print(f"Metadata saved to: {metadata_file}")
    
    return run_info


def main():
    parser = argparse.ArgumentParser(
        description="Run baseline evaluations for controller experiments"
    )
    parser.add_argument(
        "--model", "-m",
        required=True,
        help="HuggingFace model name or path (e.g., 'bigcode/starcoder2-3b')"
    )
    parser.add_argument(
        "--benchmark", "-b",
        choices=["humaneval", "mbpp"],
        default="humaneval",
        help="Benchmark to evaluate on"
    )
    parser.add_argument(
        "--mode",
        choices=["greedy", "sampling", "all"],
        default="greedy",
        help="Baseline mode to run"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("results/baselines"),
        help="Output directory for results"
    )
    parser.add_argument(
        "--num-samples", "-n",
        type=int,
        default=1,
        help="Number of samples (multi-sample aggregation not implemented here yet; use 1)"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.8,
        help="Temperature for sampling"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    if args.mode in ("greedy", "all"):
        result = run_greedy_baseline(args.model, args.benchmark, args.output_dir)
        results.append(result)
    
    if args.mode in ("sampling", "all"):
        result = run_sampling_baseline(
            args.model, 
            args.benchmark, 
            args.output_dir,
            num_samples=args.num_samples,
            temperature=args.temperature,
        )
        results.append(result)
    
    print(f"\nResults saved to: {args.output_dir}")


if __name__ == "__main__":
    main()

