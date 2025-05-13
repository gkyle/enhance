@echo off
Pushd "%~dp0"
powershell -c "src/setup/setup.ps1"

echo Starting Enhance AI...
uv run src/setup/lrcPath.py
uv run src/main.py %1
popd