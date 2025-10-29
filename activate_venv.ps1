# Activate the correct virtual environment (.venv has the SDK)
Write-Host "Activating .venv (has project-x-py SDK)..." -ForegroundColor Green
.\.venv\Scripts\Activate.ps1

Write-Host "`nSDK Version:" -ForegroundColor Cyan
python -c "import project_x_py; print('project-x-py', project_x_py.__version__)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "SDK not found!" -ForegroundColor Red
} else {
    Write-Host "`nReady to run tests!" -ForegroundColor Green
    Write-Host "Run: python test_position_event_semantics.py" -ForegroundColor Yellow
}
