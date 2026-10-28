$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try { & npm.cmd run dev; exit $LASTEXITCODE } finally { Pop-Location }
