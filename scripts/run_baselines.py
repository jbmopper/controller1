#!/usr/bin/env python3
"""
Run baseline evaluations for HumanEval and MBPP.

This script establishes the baselines needed before any controller experiments:
1. Greedy pass@1 (temp=0) - deterministic baseline
2. Sampling pass@k - upper bound with multiple samples

Usage:
    # Run greedy baseline on HumanEval with a specific model
    uv run python scripts/run_baselines.py --model <model_name> --benchmark humaneval --mode greedy
    
    # Run sampling baseline (200 samples for pass@k estimation)
    uv run python scripts/run_baselines.py --model <model_name> --benchmark humaneval --mode sampling
    
    # Run both baselines
    uv run python scripts/run_baselines.py --model <model_name> --benchmark humaneval --mode all
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config.contracts import contract_report


def get_lm_eval_command(
    model: str,
    benchmark: str,
    output_dir: Path,
    mode: str = "greedy",
    num_samples: int = 1,
    temperature: float = 0.0,
) -> list[str]:
    """Build the lm_eval command for a baseline run."""
    
    # Base command
    cmd = [
        "uv", "run", "lm_eval",
        "--model", "hf",
        "--model_args", f"pretrained={model}",
        "--tasks", benchmark,
        "--output_path", str(output_dir),
        "--log_samples",
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
    
    return {
        "mode": "greedy",
        "model": model,
        "benchmark": benchmark,
        "output_dir": str(run_dir),
        "exit_code": result.returncode,
    }


def run_sampling_baseline(
    model: str, 
    benchmark: str, 
    output_dir: Path,
    num_samples: int = 200,
    temperature: float = 0.8,
) -> dict:
    """Run sampling baseline for pass@k estimation."""
    print(f"\n{'='*60}")
    print(f"Running SAMPLING baseline: {model} on {benchmark}")
    print(f"  Temperature: {temperature}")
    print(f"  Num samples: {num_samples}")
    print(f"{'='*60}\n")
    
    run_dir = output_dir / f"sampling_n{num_samples}_t{temperature}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # For multiple samples, we'll need a custom approach
    # The lm-eval harness doesn't directly support n>1 via CLI
    # We'll document this limitation and suggest alternatives
    
    print("NOTE: For pass@k with k>1, you need to either:")
    print("  1. Modify the task YAML to set 'repeats: N'")
    print("  2. Use the Python API directly")
    print("  3. Run multiple times and aggregate")
    print()
    
    cmd = get_lm_eval_command(
        model, benchmark, run_dir, 
        mode="sampling", 
        temperature=temperature
    )
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    return {
        "mode": "sampling",
        "model": model,
        "benchmark": benchmark,
        "temperature": temperature,
        "num_samples": num_samples,
        "output_dir": str(run_dir),
        "exit_code": result.returncode,
    }


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
        default=200,
        help="Number of samples for pass@k estimation"
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
    
    # Save run metadata
    metadata_file = args.output_dir / "run_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump({
            "runs": results,
            "timestamp": datetime.now().isoformat(),
            "contracts": contract_report(),
        }, f, indent=2)
    
    print(f"\nResults saved to: {args.output_dir}")
    print(f"Metadata: {metadata_file}")


if __name__ == "__main__":
    main()

