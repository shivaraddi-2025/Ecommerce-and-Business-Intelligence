@echo off
cd /d "%~dp0"
set DATASET_PATH=.\data\raw\ecommerce_sales_raw.csv.csv
set APP_SECRET=replace-this-for-local-development
echo Starting Nexus Commerce Intelligence Backend...
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
pause
