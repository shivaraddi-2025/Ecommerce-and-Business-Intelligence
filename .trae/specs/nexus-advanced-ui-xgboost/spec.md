# Nexus Commerce Intelligence — Advanced UI Expansion + XGBoost Integration

## Problem

The current Nexus BI dashboard ships with a 7-item sidebar (Overview / Segment Analysis / Sales Analytics / Customers / Returns & Risk / Recommendations / Data Quality) and uses a single `RandomForestRegressor` for forecasting. The user requested an **advanced, expanded, professional-grade UI with four distinct menu groups** (Workspace · AI & Predictive · Data Management · Management) that mirrors a real enterprise BI platform, plus **XGBoost** as a new ML engine, **without breaking the existing dashboard**.

## Users

- **Admin role users**: Can access the entire menu including Data Management, Users & Roles, Audit Logs, Settings, and Data Import/Export.
- **Business Manager / Analyst / Viewer**: Can see the Workspace and AI & Predictive groups, but Data Management and Management sections may be read-only or hidden based on role.

## Goals

1. **Preserve the existing dashboard 100%**: every current page, chart, KPI, filter, and API call must keep working exactly as before.
2. **Expand the sidebar navigation** from 7 items → ~18+ logically-grouped items with section headers (WORKSPACE · AI & PREDICTIVE · DATA MANAGEMENT · MANAGEMENT).
3. **Every new sidebar item must route to a real, working page/section**: no dead-end stubs — each page must contain meaningful, data-driven UI.
4. **Introduce XGBoost** as a first-class ML model alongside the existing RandomForest — forecast endpoints must expose both models with side-by-side quality comparison (MAE, R², better/worse flags).
5. **Maintain the existing glass-morphism visual language**: gradients, blurred glass panels, orb background decorations, responsive layout.

## Non-Goals

- Not a backend rewrite; keep FastAPI + SQLAlchemy + pymysql architecture intact.
- Not a React framework migration; keep `vite + react` single-file App approach (add files but preserve `App.jsx` wiring).
- Not replacing RandomForest; XGBoost is additive, not a replacement.
- Not implementing full user/role CRUD editing or RBAC management UI; provide read-only Management pages with role-appropriate scaffolding.
- Not changing the existing CSV-upload or MySQL sync from the previous fix.

---

## Functional Requirements

### F1 — Sidebar Reorganization & Grouping

The sidebar MUST render four labelled groups:

- **WORKSPACE** (top): Overview · Sales Analytics · Profitability · Product Analytics · Customer Intelligence · Segment Analysis · Geographic Analysis · Returns & Risk
- **AI & PREDICTIVE**: Sales Forecast · Anomaly Detection · AI Business Advisor · Customer Prediction
- **DATA MANAGEMENT**: Database · Data Import · Data Quality · Export & Reports
- **Management**: Audit Logs · Users & Roles · Settings

### F2 — Route Mapping (Backward Compatibility)

All **original routes** (overview / segments / sales / customers / risk / recommendations / quality) MUST remain functional and render exactly the same content they do today. New keys MUST be added for the new pages.

### F3 — New WORKSPACE Pages

Each page MUST contain the specified content:

| Page | Required Content |
|---|---|
| Profitability | Profit KPIs, margin-by-category bar, profit trend line, profit-heatmap (category × region from segments API), top profitable products & customers |
| Product Analytics | Top products table, category penetration, product return rate, unit-price vs sales scatter (synthetic from data), category-wise product count |
| Customer Intelligence | Top customers table, RFM-style buckets (Monetary/Frequency synthetic recency flag), segment vs AOV, repeat-customer rate KPI |
| Geographic Analysis | Regions ranked table, cities ranked, category × region heatmap (reuse `segments/matrix`), top-city KPI strip |

Existing Overview, Sales Analytics, Segment Analysis, Returns & Risk, Recommendations, Data Quality — keep unchanged; only update VIEW_LABELS.

### F4 — AI & PREDICTIVE Pages

| Page | Required Content |
|---|---|
| **Sales Forecast** (enhanced) | Dual model selector: RandomForest (existing) vs **XGBoost** (new). Side-by-side MAE / R² comparison chart. Confidence band rendering for both. |
| Anomaly Detection | Daily sales with 3σ upper/lower bounds; flag anomalous days as cards list + overlay on line chart. Implemented via rolling-mean + rolling-std in analytics.py → new API endpoint. |
| AI Business Advisor | Natural-language-style KPI insights (rule-based templates derived from KPIs): strongest category, weakest region, risk alerts, 3 actionable recommendations with score. |
| Customer Prediction | Per-customer next-purchase value estimate, churn-risk tier, top-20 high-value predicted spenders. Stored in-memory via analytics.py → new API endpoint. |

### F5 — DATA MANAGEMENT Pages

| Page | Required Content |
|---|---|
| Database | Table row-counts from MySQL (orders, customers, products, order_items, daily_sales_agg, …) with bar chart; MySQL vs CSV record parity check; "Refresh DB Sync" button that calls the already-built `db_sync.sync_csv_to_db`. |
| Data Import | Existing CSV upload UI — keep exactly as-is (already working). Repositioned under this section. |
| Data Quality | Existing quality page — keep exactly as-is. |
| Export & Reports | Buttons to trigger CSV download of sales records / top products / top customers / daily aggregates via Blob download from API responses; report generation timestamp. |

### F6 — Management Pages (Scaffold-level but functional)

| Page | Required Content |
|---|---|
| Audit Logs | In-memory append-only list: every login, sale create/update/delete, upload, refresh action gets a timestamp + actor entry; rendered as a log table. Stored in `window.localStorage` + refreshed from the session. |
| Users & Roles | Read-only list of users (name, email, role, created_at) pulled from `/api/auth` extension OR fallback to built-in demo user cards. Role badge colour-coded. |
| Settings | Theme toggle (dark/light — default dark unchanged), forecast horizon default, dataset path display, database backend (MySQL/SQLite indicator) from `/api/health`. |

### F7 — XGBoost Integration (Backend)

- `xgboost` added to `requirements.txt`.
- `AnalyticsEngine.daily_sales_forecast()` MUST accept a `model` parameter (`"random_forest"` OR `"xgboost"`, default backward-compatible `"random_forest"`).
- New function `AnalyticsEngine.daily_sales_forecast_compare()` returning both models' outputs with: per-model MAE, R², baseline_mae, is_model_better, and `forecast` arrays.
- New endpoint `GET /api/sales/daily/forecast-compare` returning the comparison payload.
- Existing `GET /api/sales/daily/forecast` MUST continue to work unchanged (add `model` query param as optional).
- If `xgboost` import fails due to missing install, the engine MUST gracefully degrade to `random_forest` only and surface a `warning` field.

### F8 — Backward-Compatible APIs

All existing endpoints must remain unchanged in both URL and response schema. Add new endpoints and optional new fields only; never remove or rename any field.

---

## Non-Functional Requirements

### NF1 — No Dashboard Regression

- Rule: Every existing view (overview / segments / sales / customers / risk / recommendations / quality) MUST render exactly the same charts, use the same API calls, and produce identical output to the baseline implementation.
- Evidence: Opening `overview` view after changes still shows 4 KPI cards, trend line, category bar, recommendations section; no console errors.

### NF2 — Performance

- Rule: First paint of new pages MUST complete within 2× the baseline Overview-view paint time (baseline ≈ 0.5–1s on this dataset); no page should take longer than 3s for any API call chain.
- Evidence: Browser network tab shows all API calls for a page finish within 3s.

### NF3 — Dependency Safety

- Rule: If `xgboost` Python package is not installed, the app MUST still boot; the XGBoost option in the Forecast page simply shows "XGBoost not installed" with a graceful helper message and a link to install instructions.
- Evidence: Backend health check passes with and without xgboost installed.

### NF4 — Responsive Layout

- Rule: Sidebar collapses gracefully on narrow screens (<=1024px); panels remain 1-column on mobile and preserve the current responsive breakpoints from `index.css`.
- Evidence: Chrome DevTools toggle device toolbar to 768px — page scrolls vertically, no horizontal overflow.

### NF5 — Existing Auth Workflow

- Rule: Login screen, token storage, and role gating for Admin upload MUST continue to work exactly as today.
- Evidence: `demo@example.com / demo-password` logs in successfully; Data Import page still requires Admin and returns 403 otherwise.

---

## Constraints, Dependencies, Assumptions

- **Constraints**: Do not split `App.jsx` into 18 separate component files unless strictly required for maintainability; prefer grouped functional components within the same file OR add a small `pages.jsx` companion. Do not break existing CSS selectors in `index.css`.
- **Dependencies**: Add `xgboost>=2.0,<3` to `requirements.txt` only.
- **Assumptions**: MySQL stays reachable at 127.0.0.1:3306/nexus_commerce_bi as per `.env`. If MySQL unavailable, SQLite fallback continues to work; DB Management page shows backend and gracefully skips MySQL row counts.

## Open Questions

None at this time — scope is well-defined based on the provided sidebar mockup.

---

## Acceptance Criteria

| ID | Type | Description |
|---|---|---|
| AC1 | rule | Sidebar renders 4 labelled groups (WORKSPACE, AI & PREDICTIVE, DATA MANAGEMENT, MANAGEMENT) containing all 18+ items exactly as specified in F1. |
| AC2 | rule | All 7 original view keys produce visually identical pages; no existing chart, KPI, or API call path is altered (F2). |
| AC3 | rule | Every NEW sidebar key maps to a distinct view block in `renderView()` with page-specific data content per F3, F4, F5, F6. No page renders "coming soon" placeholder text. |
| AC4 | rule | `requirements.txt` contains `xgboost>=2.0,<3`; `analytics.py` imports XGBoost conditionally and exposes a comparison forecast function; new endpoint `GET /api/sales/daily/forecast-compare` returns both models with MAE, R², and per-day arrays (F7). |
| AC5 | rule | Existing `/api/sales/daily/forecast` still works without a `model` param and returns identical output to baseline implementation when `model=random_forest` or default (F7). |
| AC6 | rule | Forecast page UI has a model selector toggle (RandomForest / XGBoost / Compare) and renders MAE + R² badges + comparison chart when Compare is chosen (F4). |
| AC7 | rule | Database page under Data Management calls MySQL for table row counts, shows parity check vs CSV record count, and has a "Sync CSV → DB" button that triggers `db_sync.sync_csv_to_db` with status feedback (F5). |
| AC8 | rule | Backend runs `uvicorn` startup without `ModuleNotFoundError: No module named 'xgboost'` even if package not installed; `warning` field surfaced in compare endpoint (NF3). |
| AC9 | rule | Login, Admin upload, Sales CRUD continue to work identically; tokens stored in localStorage, Admin-only upload returns 403 for Viewer role (NF5). |
| AC10 | rubric | Layout/visual fidelity to glass-morphism style — scale 0–2; **pass threshold ≥ 1**. Anchors: 0 = inconsistent style, 1 = consistent with existing panels/orbs/KPI gradients, 2 = polished/original-level aesthetics. |
| AC11 | rubric | Page content richness and "real BI feel" — scale 0–2; **pass threshold ≥ 1**. Anchors: 0 = stubs, 1 = each new page contains ≥3 meaningful panels/KPIs/charts driven by actual data, 2 = each new page feels like a production BI report. |
| AC12 | rubric | Code maintainability and backward-safety — scale 0–2; **pass threshold ≥ 1**. Anchors: 0 = messy edits with duplicated code, 1 = clearly demarcated original-vs-new sections with additive-only edits, 2 = clean modular structure, no existing lines touched unless strictly required. |
