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

Open `http://127.0.0.1:8000` after starting the backend. The React dashboard is served from the built frontend bundle and the first sign-in registers a local Viewer account automatically. API documentation is at `/docs`.

For frontend development from the project root:

```powershell
npm install
npm run dev
```

The root `npm run dev` command delegates to the React app in `frontend/`. The Vite dev server runs on `http://127.0.0.1:5173` and talks to the FastAPI API on `http://127.0.0.1:8000`. To install frontend dependencies directly, use `npm --prefix frontend install`.

The default project dataset is `data/raw/ecommerce_sales_raw.csv.csv` with 80,000
orders. The API normalizes its lowercase source columns to the names used by
the dashboard. Dataset-backed place/city values are available in the dashboard
filter and are applied to KPI, trend, and daily sales views. Because this source
does not provide cost or profit data, profit is transparently estimated at a
30% planning margin and marked as estimated in the data-quality response.

If PowerShell has not activated the virtual environment, use the explicit
`.venv\Scripts\python.exe` command above. Running `python -m uvicorn` with a
different system Python can fail with `ModuleNotFoundError: No module named
'fastapi'`.

## Included endpoints

`/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/dashboard/kpis`, `/api/sales/trend`, `/api/sales/category`, `/api/products/top`, `/api/customers/top`, `/api/recommendations`, `/api/data/quality`, `/api/predict`, and admin-only `/api/data/upload`.

## Project phases

The profiling artifacts in `data/reports` are the evidence baseline. Next implementation phases should add deterministic cleaning outputs, persisted feature tables, trained model artifacts with validation metrics, scheduled reports, and a production database connection. The dashboard has been converted to a React + Vite frontend with component-based rendering and a production build pipeline; the backend still exposes the analytics API and can serve the built bundle.
Run tests with:

```powershell
python -m pytest
```