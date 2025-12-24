#!/usr/bin/env python3
"""
Controller1: Research on controllers and decoding strategies for LLMs.

This is the main entry point. Run with --help for options.
"""

import argparse
import sys


def show_protocol():
    """Display the evaluation protocol."""
    from config import DEFAULT_PROTOCOL
    print(DEFAULT_PROTOCOL.summary())


def show_prompt_contract(benchmark: str = "humaneval"):
    """Display the prompt contract for a benchmark."""
    from config import get_prompt_config
    
    config = get_prompt_config(benchmark)
    print(f"\n{'='*60}")
    print(f"PROMPT CONTRACT: {benchmark.upper()}")
    print(f"{'='*60}")
    print(f"\nDataset: {config.dataset_path}")
    print(f"Split: {config.split}")
    print(f"\nTemplate: {config.doc_to_text_template}")
    print(f"\nStop sequences: {config.stop_sequences}")
    print(f"\nGeneration:")
    print(f"  max_tokens: {getattr(config, 'max_gen_tokens', 'default')}")
    print(f"  do_sample: {config.do_sample}")
    if hasattr(config, 'num_fewshot'):
        print(f"  num_fewshot: {config.num_fewshot}")
    print()


def show_sandbox_config():
    """Display sandbox configuration."""
    from config import DEFAULT_SANDBOX_CONFIG, DEV_SANDBOX_CONFIG
    
    print(f"\n{'='*60}")
    print("SANDBOX CONFIGURATION")
    print(f"{'='*60}")
    
    print("\nDEFAULT (Production):")
    print(f"  Mode: {DEFAULT_SANDBOX_CONFIG.mode}")
    print(f"  Timeout: {DEFAULT_SANDBOX_CONFIG.timeout_seconds}s")
    print(f"  Memory: {DEFAULT_SANDBOX_CONFIG.memory_limit_mb}MB")
    print(f"  Network: {DEFAULT_SANDBOX_CONFIG.allow_network}")
    
    print("\nDEVELOPMENT:")
    print(f"  Mode: {DEV_SANDBOX_CONFIG.mode}")
    print(f"  Timeout: {DEV_SANDBOX_CONFIG.timeout_seconds}s")
    print(f"  Memory: {DEV_SANDBOX_CONFIG.memory_limit_mb}MB")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Controller1: LLM decoding research toolkit"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Protocol command
    subparsers.add_parser("protocol", help="Show evaluation protocol")
    
    # Prompt command
    prompt_parser = subparsers.add_parser("prompt", help="Show prompt contract")
    prompt_parser.add_argument(
        "--benchmark", "-b",
        choices=["humaneval", "mbpp"],
        default="humaneval",
        help="Benchmark to show"
    )
    
    # Sandbox command
    subparsers.add_parser("sandbox", help="Show sandbox configuration")
    
    # Info command - show all
    subparsers.add_parser("info", help="Show all configurations")
    
    args = parser.parse_args()
    
    if args.command == "protocol":
        show_protocol()
    elif args.command == "prompt":
        show_prompt_contract(args.benchmark)
    elif args.command == "sandbox":
        show_sandbox_config()
    elif args.command == "info":
        show_protocol()
        show_prompt_contract("humaneval")
        show_prompt_contract("mbpp")
        show_sandbox_config()
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("Quick start:")
        print("  uv run python main.py info      # Show all configurations")
        print("  uv run python main.py protocol  # Show evaluation protocol")
        print("="*60)


if __name__ == "__main__":
    main()
