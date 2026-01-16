"""
Inference Configuration

Defines runtime inference settings that can affect reproducibility.
Changes here (dtype, batch size, etc.) may affect numerical results,
so they are tracked via contract fingerprints.
"""

from dataclasses import dataclass
from typing import Literal


DType = Literal["float32", "float16", "bfloat16", "auto"]


@dataclass
class InferenceConfig:
    """Configuration for model inference.
    
    These settings can affect numerical results and should be tracked
    for reproducibility. Changes require explicit fingerprint updates.
    """
    
    # Model precision - affects numerical stability and memory usage
    # float32: Most stable, 2x memory
    # float16: Fast on most GPUs, can have precision issues
    # bfloat16: Good balance, but MPS support is spotty
    # auto: Use model's native dtype (not recommended for reproducibility)
    dtype: DType = "float32"
    
    # Batch size for inference - affects throughput, not results
    # (Included for completeness, but shouldn't affect outputs)
    batch_size: int = 4
    
    # Maximum new tokens to generate
    # 512 is plenty for HumanEval/MBPP (most solutions < 256 tokens)
    max_new_tokens: int = 512
    
    # Whether to trust remote code (required for some models)
    trust_remote_code: bool = False


# Default configuration - stable settings for reproducibility
DEFAULT_INFERENCE_CONFIG = InferenceConfig(
    dtype="float32",
    batch_size=4,
    max_new_tokens=512,
    trust_remote_code=False,
)
