@echo off
Pushd "%~dp0"
powershell -c "src/setup/setup.ps1"

echo Starting Enhance AI...
uv run --no-sync src/setup/lrcPath.py
uv run --no-sync src/main.py %1
popd