# syntax=docker/dockerfile:1.6
FROM mcr.microsoft.com/devcontainers/python:3.11

ENV DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy

# Install system packages (extend as needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    exiftool \
    mediainfo \
    unzip \
    ripgrep \
    fd-find \
    curl \
    ca-certificates \
    git \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Symlink fd (fd-find installs 'fdfind')
RUN if [ ! -e /usr/local/bin/fd ]; then ln -s /usr/bin/fdfind /usr/local/bin/fd; fi

## Install uv via PyPI (avoids curl TLS issues in some host setups)
# Upstream provides prebuilt wheels; this is simpler and more reliable cross-platform.
# If a native build is ever required, ensure build-essential and rust toolchain are present.
RUN pip install --no-cache-dir uv

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

# Install DuckDB CLI (arch-aware, resilient to asset name differences)
ARG DUCKDB_CLI_VERSION=1.3.2
RUN set -eux; \
    arch="$(uname -m)"; \
    case "$arch" in \
      x86_64) candidates="linux-amd64" ;; \
      aarch64|arm64) candidates="linux-aarch64 linux-arm64" ;; \
      *) echo "Unsupported arch: $arch" >&2; exit 1 ;; \
    esac; \
    success=0; \
    for target in $candidates; do \
      url="https://github.com/duckdb/duckdb/releases/download/v${DUCKDB_CLI_VERSION}/duckdb_cli-${target}.zip"; \
      echo "Trying DuckDB CLI from: $url"; \
      if curl -fSL "$url" -o /tmp/duckdb_cli.zip; then \
        unzip -o /tmp/duckdb_cli.zip -d /usr/local/bin; \
        rm -f /tmp/duckdb_cli.zip; \
        chmod +x /usr/local/bin/duckdb; \
        success=1; \
        break; \
      fi; \
    done; \
    if [ "$success" -ne 1 ]; then \
      echo "Failed to download DuckDB CLI for arch $arch" >&2; \
      exit 1; \
    fi; \
    /usr/local/bin/duckdb --version

# Keep the container alive for VS Code to attach
CMD ["tail", "-f", "/dev/null"]
