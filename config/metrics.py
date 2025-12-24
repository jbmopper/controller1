"""
Metrics Configuration

Defines the evaluation metrics and baselines for controller experiments.

Key metrics:
1. pass@1 (deterministic, temp=0) - Baseline greedy performance
2. pass@k (sampling) - Upper bound with multiple samples  
3. controller pass@1 - Controller-guided single attempt
4. compute-matched pass@k - Fair comparison with same compute budget

IMPORTANT: When comparing controller methods, you must match compute budgets.
A controller that uses N forward passes should be compared against pass@k
with the same number of samples, not against greedy pass@1.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class MetricConfig:
    """Configuration for a single metric."""
    name: str
    k: int = 1
    temperature: float = 0.0
    num_samples: int = 1
    description: str = ""


@dataclass
class BaselineConfig:
    """Configuration for baseline evaluations."""
    
    # Deterministic baseline: greedy decoding
    greedy: MetricConfig = field(default_factory=lambda: MetricConfig(
        name="pass@1_greedy",
        k=1,
        temperature=0.0,
        num_samples=1,
        description="Greedy decoding (temp=0), single sample. Primary baseline."
    ))
    
    # Sampling baselines at different k values
    # Standard temperatures from the literature
    sampling_temperature: float = 0.8
    
    # pass@k for k in [1, 10, 100]
    # Requires num_samples >= k for unbiased estimation
    pass_at_k_values: tuple[int, ...] = (1, 10, 100)
    
    # Number of samples for pass@k estimation
    # 200 samples is standard for estimating up to pass@100
    num_samples_for_estimation: int = 200
    
    def get_sampling_metrics(self) -> list[MetricConfig]:
        """Get sampling baseline metrics."""
        return [
            MetricConfig(
                name=f"pass@{k}_sampling",
                k=k,
                temperature=self.sampling_temperature,
                num_samples=self.num_samples_for_estimation,
                description=f"pass@{k} with temp={self.sampling_temperature}, n={self.num_samples_for_estimation}"
            )
            for k in self.pass_at_k_values
        ]


@dataclass
class ControllerMetricConfig:
    """Configuration for controller evaluation metrics."""
    
    # Number of candidates the controller considers
    num_candidates: int = 10
    
    # Temperature for candidate generation
    candidate_temperature: float = 0.8
    
    # Whether controller uses additional forward passes for selection
    # This affects compute budget matching
    selection_forward_passes: int = 0
    
    @property
    def total_forward_passes(self) -> int:
        """Total forward passes for compute budget comparison."""
        return self.num_candidates + self.selection_forward_passes
    
    def get_compute_matched_baseline(self) -> MetricConfig:
        """Get the compute-matched sampling baseline for fair comparison."""
        return MetricConfig(
            name=f"pass@1_from_{self.total_forward_passes}_samples",
            k=1,
            temperature=0.8,
            num_samples=self.total_forward_passes,
            description=(
                f"Sampling baseline with same compute budget as controller "
                f"({self.total_forward_passes} forward passes)"
            )
        )


# Standard evaluation protocol
@dataclass
class EvaluationProtocol:
    """
    Complete evaluation protocol for controller experiments.
    
    This ensures fair comparisons by:
    1. Establishing deterministic baseline (pass@1, temp=0)
    2. Establishing sampling upper bounds (pass@k)
    3. Matching compute budgets for controller comparisons
    """
    
    baselines: BaselineConfig = field(default_factory=BaselineConfig)
    controller: ControllerMetricConfig = field(default_factory=ControllerMetricConfig)
    
    # Benchmark to evaluate on
    benchmark: Literal["humaneval", "mbpp"] = "humaneval"
    
    # Random seed for reproducibility
    seed: int = 42
    
    # Number of evaluation runs for confidence intervals
    num_runs: int = 1
    
    def get_all_metrics(self) -> list[MetricConfig]:
        """Get all metrics to compute."""
        metrics = [self.baselines.greedy]
        metrics.extend(self.baselines.get_sampling_metrics())
        metrics.append(self.controller.get_compute_matched_baseline())
        return metrics
    
    def summary(self) -> str:
        """Human-readable summary of the evaluation protocol."""
        lines = [
            "=" * 60,
            "EVALUATION PROTOCOL",
            "=" * 60,
            f"Benchmark: {self.benchmark}",
            f"Seed: {self.seed}",
            "",
            "BASELINES:",
            f"  - Greedy (temp=0): pass@1",
            f"  - Sampling (temp={self.baselines.sampling_temperature}):",
        ]
        for k in self.baselines.pass_at_k_values:
            lines.append(f"      pass@{k} (n={self.baselines.num_samples_for_estimation})")
        
        lines.extend([
            "",
            "CONTROLLER:",
            f"  - Candidates: {self.controller.num_candidates}",
            f"  - Selection passes: {self.controller.selection_forward_passes}",
            f"  - Total compute: {self.controller.total_forward_passes} forward passes",
            "",
            "FAIR COMPARISON:",
            f"  Controller vs pass@1 from {self.controller.total_forward_passes} samples",
            "=" * 60,
        ])
        return "\n".join(lines)


# Default protocol
DEFAULT_PROTOCOL = EvaluationProtocol()

if __name__ == "__main__":
    print(DEFAULT_PROTOCOL.summary())

