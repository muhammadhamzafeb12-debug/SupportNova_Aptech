Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "🚀 Starting SupportNova (Backend + Frontend)..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

# Start Backend
Write-Host "Starting Backend Server on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000"

Start-Sleep -Seconds 2

# Start Frontend
Write-Host "Starting Frontend UI on http://localhost:3000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Start-Sleep -Seconds 2

# Open browser
Write-Host "Opening SupportNova App in your browser..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "✅ SupportNova is running!" -ForegroundColor Green
Write-Host "- Backend API: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "- Frontend App: http://localhost:3000" -ForegroundColor Gray
Write-Host "========================================================" -ForegroundColor Cyan
