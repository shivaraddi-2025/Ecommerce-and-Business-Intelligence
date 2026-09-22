# Nexus Commerce Intelligence

Runnable decision-support foundation for the supplied e-commerce transaction dataset. The current release includes dataset-backed analytics, quality metrics, role-aware authentication, prediction support, recommendations, a normalized MySQL schema, REST APIs, and a responsive browser dashboard.

## Run

From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATASET_PATH = '.\data\raw\ecommerce_sales_raw.csv.csv'
$env:APP_SECRET = 'replace-this-for-local-development'
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000`. The first sign-in registers a local Viewer account automatically. API documentation is at `/docs`.

The default project dataset is `data/raw/ecommerce_sales_raw.csv.csv` with 80,000
orders. The API normalizes its lowercase source columns to the names used by
the dashboard. Dataset-backed place/city values are available in the dashboard
filter and are applied to KPI, trend, and daily sales views. Because this source does not provide cost or profit data,
`Profit` and profit-based predictions are reported as zero rather than being
invented from sales.

If PowerShell has not activated the virtual environment, use the explicit
`.venv\Scripts\python.exe` command above. Running `python -m uvicorn` with a
different system Python can fail with `ModuleNotFoundError: No module named
'fastapi'`.

## Included endpoints

`/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/dashboard/kpis`, `/api/sales/trend`, `/api/sales/category`, `/api/products/top`, `/api/customers/top`, `/api/recommendations`, `/api/data/quality`, `/api/predict`, and admin-only `/api/data/upload`.

## Project phases

The profiling artifacts in `data/reports` are the evidence baseline. Next implementation phases should add deterministic cleaning outputs, persisted feature tables, trained model artifacts with validation metrics, scheduled reports, and a production database connection. The dashboard currently uses CDN Chart.js for a zero-build local demo; production deployment should pin and bundle frontend assets.

Run tests with:

```powershell
python -m pytest
```