# syntax=docker/dockerfile:1.6
FROM mcr.microsoft.com/devcontainers/python:3.11

ENV DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy

# Install system packages (extend as needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    exiftool \
    mediainfo \
    duckdb \
    ripgrep \
    fd-find \
    curl \
    ca-certificates \
    git \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Symlink fd (fd-find installs 'fdfind')
RUN if [ ! -e /usr/local/bin/fd ]; then ln -s /usr/bin/fdfind /usr/local/bin/fd; fi

# Install uv (fast Python package/dependency manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    rm -rf /root/.local

# Install baseline dev tooling with pip during image build
RUN pip install --no-cache-dir \
    pytest pytest-cov \
    mypy \
    ruff \
    black \
    build \
    duckdb \
    pandas

# Create scripts directory placeholder (so postCreateCommand doesn't fail)
RUN mkdir -p /workspaces/disk-catalogue/scripts

WORKDIR /workspaces/disk-catalogue

# Keep the container alive for VS Code to attach
CMD ["tail", "-f", "/dev/null"]
