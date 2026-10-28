param([int]$Port = 8501)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonCandidates = @((Join-Path $projectRoot ".venv-streamlit/Scripts/python.exe"), (Join-Path $projectRoot "backend/.venv/Scripts/python.exe"))
$pythonRunner = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $pythonRunner) { $pythonRunner = "python" }
& $pythonRunner -m streamlit run (Join-Path $projectRoot "streamlit_app.py") --server.address 127.0.0.1 --server.port $Port
exit $LASTEXITCODE
