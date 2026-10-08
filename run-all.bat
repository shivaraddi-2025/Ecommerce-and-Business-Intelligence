@echo off
cd /d "%~dp0"
echo Starting Nexus Commerce Intelligence (Backend + Frontend)...
start "Nexus Backend (FastAPI)" cmd /k "set DATASET_PATH=.\data\raw\ecommerce_sales_raw.csv.csv && set APP_SECRET=replace-this-for-local-development && .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul
start "Nexus Frontend (Vite)" cmd /k "npm --prefix frontend run dev"
echo.
echo ========================================================
echo   Backend running at:  http://127.0.0.1:8000
echo   Frontend running at: http://localhost:5173
echo ========================================================
