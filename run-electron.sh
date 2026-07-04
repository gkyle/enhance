#!/bin/bash

# Launch the experimental Electron UI for Enhance AI.
#
# Usage:
#   ./run-electron.sh [IMAGE]
#
#   IMAGE   Optional path to a base image to load at startup (jpg/png/tiff).
#           Relative paths are resolved against your current directory.
#
# The Electron main process spawns the Python backend (via `uv run uvicorn`)
# on a free port, so the same uv-managed environment as run.sh is used.

set -e

# Resolve the image argument to an absolute path (before we change directory),
# so it stays valid regardless of the backend's working directory.
IMAGE_ARG=""
if [ -n "$1" ]; then
    if [ ! -e "$1" ]; then
        echo "Warning: image path does not exist: $1" >&2
    fi
    # realpath -m resolves without requiring the path to exist.
    IMAGE_ARG="$(realpath -m "$1")"
fi

# Change directory to the script's location (repo root).
cd "$(dirname "$0")"

# Install UV if not already installed.
uv_version=`uv -V`
if [ "$uv_version" = "" ]; then
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi;

# Check for compatible GPU and sync the matching torch variant (mirrors run.sh).
echo "Determining correct configuration for your GPU..."
torch_variant=`uv run --no-sync src/setup/probeGPU.py`
if [ "$torch_variant" = "" ]; then
    torch_variant="cpu"
fi;
if [ "$torch_variant" = "cpu" ]; then
    echo "Setup did not find a compatible GPU. Continuing with CPU-only dependencies."
else
    echo "Using torch variant: $torch_variant"
fi;
uv sync --extra $torch_variant

# Ensure Electron dependencies are installed.
cd electron
if [ ! -d "node_modules" ]; then
    echo "Installing Electron dependencies..."
    npm install
fi;

# Launch. Pass the startup image (if any) through to main.js.
echo "Starting Enhance AI (Electron)..."
if [ -n "$IMAGE_ARG" ]; then
    npm start -- "$IMAGE_ARG"
else
    npm start
fi
