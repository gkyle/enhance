#!/bin/sh

# Install UV if not already installed
uv_version=`uv -V`
if [ "$uv_version" = "" ]; then 
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi;

# Check for CUDA GPU.
echo "Determining correct configuration for your GPU..."
torch_variant=`uv run --no-sync src/setup/probeGPU.py`
if [ "$torch_variant" = "" ]; then 
    torch_variant="cpu"
    echo "Install did not find a CUDA compatible GPU. Install will continue with CPU-only dependencies. You can re-run after installing drivers or CUDA Toolkit to enable GPU support."
else
    echo "Using torch variant: $torch_variant"
fi;

# Sync with final GPU configuration
uv sync --extra $torch_variant

# Run
echo "Starting Enhance AI..."
uv run --no-sync src/main.py $*