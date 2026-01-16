"""
Configuration module for controller experiments.

This module locks down the three critical elements for reproducible research:
1. Prompt contract - exact prompt formats for HumanEval/MBPP
2. Sandbox configuration - how generated code is executed
3. Metrics - what we measure and how we compare

Any changes to these configurations should be documented and justified.
"""

from .prompts import (
    HumanEvalPromptConfig,
    MBPPPromptConfig,
    MBPP_FEWSHOT_EXAMPLES,
    BenchmarkType,
    get_prompt_config,
)
from .sandbox import (
    SandboxConfig,
    ExecutionMode,
    DEFAULT_SANDBOX_CONFIG,
    DEV_SANDBOX_CONFIG,
    get_docker_run_command,
)
from .metrics import (
    MetricConfig,
    BaselineConfig,
    ControllerMetricConfig,
    EvaluationProtocol,
    DEFAULT_PROTOCOL,
)
from .inference import (
    InferenceConfig,
    DType,
    DEFAULT_INFERENCE_CONFIG,
)

__all__ = [
    # Prompts
    "HumanEvalPromptConfig",
    "MBPPPromptConfig", 
    "MBPP_FEWSHOT_EXAMPLES",
    "BenchmarkType",
    "get_prompt_config",
    # Sandbox
    "SandboxConfig",
    "ExecutionMode",
    "DEFAULT_SANDBOX_CONFIG",
    "DEV_SANDBOX_CONFIG",
    "get_docker_run_command",
    # Metrics
    "MetricConfig",
    "BaselineConfig",
    "ControllerMetricConfig",
    "EvaluationProtocol",
    "DEFAULT_PROTOCOL",
    # Inference
    "InferenceConfig",
    "DType",
    "DEFAULT_INFERENCE_CONFIG",
]

