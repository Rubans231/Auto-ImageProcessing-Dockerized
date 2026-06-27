# ==============================================================================
# BASE RUNTIME LAYER
# ==============================================================================
# Use a lightweight NVIDIA CUDA base with runtime acceleration
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# Prevent interactive prompts during apt package execution loops
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# ==============================================================================
# SYSTEM PACKAGE INSTALLATION & CLEANUP (Best Practice)
# ==============================================================================
# Updates and unzips core toolchains, clearing cache lists in a single layer pass
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Inject Rust-powered 'uv' globally from its official distribution mirror
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the primary environment directory inside the container
WORKDIR /app

# Install project microservice dependencies globally inside the container space
RUN uv pip install --system comfy-cli watchdog opencv-python-headless numpy

# ==============================================================================
# HEADLESS COMFYUI ENGINE PROVISIONING
# ==============================================================================
# Define a build-time argument that defaults to nvidia but can be overridden
ARG GPU_TYPE=nvidia

# Robust network environment configs to stop pypi.nvidia.com timeout drops
ENV UV_HTTP_TIMEOUT=300
ENV UV_CONCURRENT_DOWNLOADS=4

# Pull down and build the core ComfyUI engine natively
RUN comfy install --${GPU_TYPE} --fast-deps

# ==============================================================================
# APP CODE ORCHESTRATION
# ==============================================================================
# Copy local source structures across the operational container boundary
COPY src/ ./src/
COPY workflows/ ./workflows/
COPY entrypoint.sh ./

# Execute our multi-process bash orchestrator script
ENTRYPOINT ["./entrypoint.sh"]
