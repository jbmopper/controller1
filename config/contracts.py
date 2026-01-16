"""
Contract Fingerprints (Prompt/Sandbox/Metrics)

The goal is to make it *impossible* to accidentally change the evaluation setup
without noticing. Small wrapper/prompt tweaks can swing HumanEval/MBPP scores.

We therefore compute stable fingerprints (sha256) over the config objects that
define:
- prompt contract (templates, stop sequences, few-shot examples pointer)
- sandbox assumptions (docker flags, limits, network policy, image)
- metric/protocol definitions (compute budget comparison logic)

Tests assert these fingerprints, so any drift requires an explicit update.
"""

import dataclasses
import hashlib
import json
from typing import Any
from pathlib import Path

from .inference import DEFAULT_INFERENCE_CONFIG, InferenceConfig
from .metrics import DEFAULT_PROTOCOL, EvaluationProtocol
from .prompts import BenchmarkType, get_prompt_config
from .sandbox import DEFAULT_SANDBOX_CONFIG, SandboxConfig


def _stable_json(obj: Any) -> str:
    """
    Convert `obj` to a stable JSON string suitable for hashing.

    Rules:
    - dataclasses -> asdict
    - tuples -> lists
    - dict keys sorted
    """

    def default(o: Any) -> Any:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, tuple):
            return list(o)
        if isinstance(o, Path):
            return str(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=default)


def fingerprint_json(obj: Any) -> str:
    """Return sha256 hex digest of a stable JSON representation of `obj`."""
    payload = _stable_json(obj).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def prompt_contract_fingerprint(benchmark: BenchmarkType) -> str:
    """
    Fingerprint of the *prompt contract* for a benchmark.

    Note: This intentionally fingerprints only our local contract object. If you
    want to claim alignment with lm-eval, pin lm-eval to a commit (uv.lock) and
    treat any update as a contract change.
    """
    cfg = get_prompt_config(benchmark)
    return fingerprint_json(cfg)


def sandbox_contract_fingerprint(config: SandboxConfig | None = None) -> str:
    """Fingerprint of the sandbox config used for executing generated code."""
    return fingerprint_json(config or DEFAULT_SANDBOX_CONFIG)


def protocol_fingerprint(protocol: EvaluationProtocol | None = None) -> str:
    """Fingerprint of the evaluation protocol (metrics + compute matching)."""
    return fingerprint_json(protocol or DEFAULT_PROTOCOL)


def inference_contract_fingerprint(config: InferenceConfig | None = None) -> str:
    """Fingerprint of the inference config (dtype, batch size, etc.)."""
    return fingerprint_json(config or DEFAULT_INFERENCE_CONFIG)


def contract_report() -> dict[str, str]:
    """Convenience: all key contract fingerprints."""
    return {
        "prompt.humaneval": prompt_contract_fingerprint("humaneval"),
        "prompt.mbpp": prompt_contract_fingerprint("mbpp"),
        "sandbox.default": sandbox_contract_fingerprint(DEFAULT_SANDBOX_CONFIG),
        "protocol.default": protocol_fingerprint(DEFAULT_PROTOCOL),
        "inference.default": inference_contract_fingerprint(DEFAULT_INFERENCE_CONFIG),
    }


