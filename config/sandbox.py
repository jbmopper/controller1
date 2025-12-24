"""
Execution Sandbox Configuration

Defines how generated code is executed for evaluation.
This is critical for safety and reproducibility.

Options:
1. Docker (recommended for isolation)
2. Firejail (Linux-only, lighter weight)
3. Direct execution (only for trusted code / debugging)

NOTE: The baseline runner currently shells out to `lm_eval` (lm-evaluation-harness).
That harness executes generated code using its own runner (typically a local
multiprocessing/subprocess-based sandbox).

This module defines *our* intended isolation policy for controller experiments.
If/when we integrate a custom evaluator, it should use this config to execute
untrusted code inside Docker (or firejail on Linux).
"""

from dataclasses import dataclass, field
from typing import Literal
from pathlib import Path


ExecutionMode = Literal["docker", "firejail", "direct"]


@dataclass
class SandboxConfig:
    """Configuration for code execution sandbox."""
    
    # Execution mode
    mode: ExecutionMode = "docker"
    
    # Timeout per test case (seconds)
    timeout_seconds: float = 3.0
    
    # Memory limit (MB)
    memory_limit_mb: int = 512
    
    # CPU limit (number of cores)
    cpu_limit: int = 1
    
    # Network access (should almost always be False)
    allow_network: bool = False
    
    # Docker-specific settings
    # Default points at this repo's Dockerfile (`docker build -t controller1-sandbox .`)
    # so our execution environment is explicit and reproducible.
    docker_image: str = "controller1-sandbox"
    # Use a numeric UID:GID so it works across images (our Dockerfile uses uid=1000).
    docker_user: str = "1000:1000"
    
    # Firejail-specific settings (Linux only)
    firejail_profile: str | None = None
    
    # Paths
    temp_dir: Path = field(default_factory=lambda: Path("/tmp/code_eval"))
    
    def validate(self) -> None:
        """Validate configuration."""
        if self.mode == "direct":
            import warnings
            warnings.warn(
                "Running in 'direct' mode - generated code will execute without isolation! "
                "This is only safe for trusted code or debugging. "
                "Use 'docker' or 'firejail' for untrusted code.",
                RuntimeWarning
            )
        
        if self.allow_network:
            import warnings
            warnings.warn(
                "Network access is enabled for code execution. "
                "This is a security risk and may affect reproducibility.",
                RuntimeWarning
            )


# Default configuration - Docker-based isolation
DEFAULT_SANDBOX_CONFIG = SandboxConfig(
    mode="docker",
    timeout_seconds=3.0,
    memory_limit_mb=512,
    allow_network=False,
    docker_image="controller1-sandbox",
)


# Development configuration - direct execution with warnings
DEV_SANDBOX_CONFIG = SandboxConfig(
    mode="direct",
    timeout_seconds=5.0,
    memory_limit_mb=1024,
    allow_network=False,
)


def get_docker_run_command(config: SandboxConfig, code_file: Path) -> list[str]:
    """Generate Docker run command for isolated code execution."""
    cmd = [
        "docker", "run",
        "--rm",  # Remove container after execution
        "--network=none" if not config.allow_network else "",
        f"--memory={config.memory_limit_mb}m",
        f"--cpus={config.cpu_limit}",
        f"--user={config.docker_user}",
        "--read-only",  # Read-only root filesystem
        "--tmpfs=/tmp:size=64m",  # Writable /tmp with size limit
        "-v", f"{code_file.parent}:/code:ro",  # Mount code as read-only
        config.docker_image,
        "python", f"/code/{code_file.name}",
    ]
    return [c for c in cmd if c]  # Filter empty strings


# Dockerfile for custom evaluation environment
DOCKERFILE_TEMPLATE = '''
# Pin to specific Python version for reproducibility
FROM python:3.13.1-slim-bookworm

# Security: run as non-root user
RUN useradd -m -s /bin/bash -u 1000 evaluator
USER evaluator

# Minimal dependencies for code evaluation
# Add any standard library extensions here if needed

WORKDIR /code
'''

