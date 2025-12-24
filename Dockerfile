# Dockerfile for isolated code execution
# Used by the sandbox to safely execute generated code

FROM python:3.11-slim

# Security: Create non-root user for execution
RUN useradd -m -s /bin/bash -u 1000 evaluator

# Install minimal dependencies
# Keep this minimal - generated code should only use stdlib
RUN pip install --no-cache-dir \
    numpy \
    && rm -rf /root/.cache

# Set resource limits via Docker run flags, not here
# This Dockerfile just sets up the base image

# Security hardening
RUN chmod 755 /home/evaluator

# Switch to non-root user
USER evaluator
WORKDIR /home/evaluator

# Default command - will be overridden
CMD ["python", "--version"]

