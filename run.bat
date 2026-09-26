@echo off
echo ========================================================
echo 🚀 Starting SupportNova (Backend + Frontend)...
echo ========================================================

:: Start Backend in a new window
echo Starting Backend Server on http://localhost:8000 ...
start "SupportNova Backend" powershell -NoExit -Command "cd '%~dp0'; .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000"

:: Wait 2 seconds for backend to initialize
timeout /t 2 /nobreak >nul

:: Start Frontend in a new window
echo Starting Frontend UI on http://localhost:3000 ...
start "SupportNova Frontend" powershell -NoExit -Command "cd '%~dp0frontend'; npm run dev"

:: Wait 3 seconds and open browser
timeout /t 3 /nobreak >nul
echo Opening SupportNova App in your browser...
start http://localhost:3000

echo ========================================================
echo ✅ SupportNova is running!
echo - Backend API: http://localhost:8000/docs
echo - Frontend App: http://localhost:3000
echo ========================================================
