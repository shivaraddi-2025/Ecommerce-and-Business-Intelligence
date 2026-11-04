Set-Location $PSScriptRoot
$env:APP_SECRET = "replace-this-for-local-development"
Write-Host "Starting Nexus Commerce Intelligence Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
& "$PSScriptRoot\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
