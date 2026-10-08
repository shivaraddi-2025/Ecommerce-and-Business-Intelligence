# Nexus Commerce Intelligence — Advanced UI + XGBoost Implementation Tasks

## Traceability

Every Acceptance Criterion in `spec.md` maps to one or more tasks below. Task TR links list the ACs they directly satisfy.

---

## Task 1: Backend — Add XGBoost support (graceful import + dual forecast engine)

**Priority**: high
**Status**: pending
**Parent ACs**: AC4, AC5, AC8

### Scope
- `backend/app/analytics.py`:
  - Wrap `import xgboost` in try/except, set a `self.has_xgboost` instance flag.
  - Add optional `model: str = "random_forest"` parameter to `forecast_daily_sales()`.
  - Add new method `forecast_daily_sales_compare(...)` returning `{ random_forest: {...}, xgboost: {...}, meta: {...} }`.
  - Preserve 100% of existing behaviour when `model` param absent.
- `requirements.txt`: add `xgboost>=2.0,<3`.
- `backend/app/main.py`: add `GET /api/sales/daily/forecast-compare` endpoint (wraps compare function; passes filters + horizon + optional model params). Existing `/api/sales/daily/forecast` adds optional `model` query param (default `"random_forest"`).

### Test Requirements
| TR | Type | Condition |
|---|---|---|
| TR1.1 | rule | `python -m py_compile backend/app/analytics.py backend/app/main.py` passes. |
| TR1.2 | rule | Running `GET /api/sales/daily/forecast?date=2025-06-15&days=7` returns identical shape to baseline baseline (keys: forecast, today_sales, confidence, etc.). |
| TR1.3 | rule | Running `GET /api/sales/daily/forecast?model=xgboost&days=7` either returns an xgboost forecast OR (if xgboost not installed) returns RF with `warning: "xgboost not installed; used random_forest fallback"`. |
| TR1.4 | rule | Running `GET /api/sales/daily/forecast-compare?days=7` returns top-level keys `random_forest` and `xgboost`, plus `meta.has_xgboost`, `meta.best_model`, `meta.mae_rf`, `meta.mae_xgb` (or `null` when XGB unavailable). |

---

## Task 2: Backend — Add new analytics endpoints for new BI pages

**Priority**: high
**Status**: pending
**Parent ACs**: AC3, F4, F5, F6

### Scope
Add new endpoints/functions without modifying any existing response schemas:

- `analytics.py` → add methods:
  - `anomaly_daily(region, category, year, city, customer_segment)` → `{ daily: [{date, revenue, lower, upper, is_anomaly, z_score}], anomalies_summary: [...] }`. Implement rolling μ ± 3σ threshold with 14-day window.
  - `ai_business_advisor_kpis(region, category, year)` → rule-based insights array `[{insight_id, type, title, detail, severity, action, score}]` (derived from strongest/weakest category, return risk, top region, lagging region, etc.).
  - `customer_predictions(top_n, min_spend)` → `[{customer_id, customer_name, predicted_next_value, churn_risk, lifetime_value, tier, segment}]` using RFM-style heuristics + 30% margin projection (deterministic, label clearly as heuristic "Prediction").
  - `db_status_summary()` → uses `db_sync.db_conn` context (try/except) to return row counts per star-schema table; CSV record count from `len(self.frame)`; parity flag `csv_matches_db: bool` and `diff_count`.
- `main.py` → add endpoints:
  - `GET /api/analytics/anomalies` (filters: region, category, year, city, customer_segment)
  - `GET /api/ai/advisor`
  - `GET /api/analytics/customer-predictions` (query params: `top_n`, default 50)
  - `GET /api/database/status` (Admin-only per role; returns table counts, CSV count, parity)
  - `POST /api/database/sync` (Admin-only; calls `db_sync.sync_csv_to_db()` with current DATASET path; returns counts + status)
  - `GET /api/management/users` (Admin-only; returns list from users table via SQLAlchemy)
  - `GET /api/health` unchanged but add optional `role` and `db_backend` — already exists, no change.

### Test Requirements
| TR | Type | Condition |
|---|---|---|
| TR2.1 | rule | All 6 new endpoints return HTTP 200 with valid JSON; no import errors. |
| TR2.2 | rule | `/api/database/status` shows MySQL or SQLite backend correctly; row counts are integers >= 0. |
| TR2.3 | rule | `/api/ai/advisor` returns `insights` array with >= 5 items, each with `type/title/detail/score`. |
| TR2.4 | rule | `/api/analytics/anomalies` returns `daily` array with boolean `is_anomaly` flag on every row. |

---

## Task 3: Frontend — Sidebar & routing skeleton (preserve 7 original views verbatim)

**Priority**: high
**Status**: pending
**Parent ACs**: AC1, AC2, AC12

### Scope
- `App.jsx`:
  - Replace `navItems` (7 entries) with a **nested grouped array** structure `navGroups` → `[{group: 'WORKSPACE', items: [{key, label, icon}, ...]}, ...]`.
  - Replace simple `<nav>` rendering with grouped rendering: group label as uppercase eyebrow, then the items inside. Keep exact same selected-item highlight logic.
  - Extend `VIEW_LABELS` to map ALL 18+ new keys (profitability / products / customers2 / geographic / forecast / anomalies / advisor / cust_prediction / database / dataimport / export / audit / users / settings).
  - Keep existing original 7 view-cases in `renderView()` switch unchanged (overview, segments, sales, customers, risk, recommendations, quality); they MUST execute exactly the same code path they do today.
  - Add new `switch` cases for the new keys after the existing ones — DO NOT move or refactor existing case blocks.
- `index.css`:
  - Add `.nav-group-label` styling (light-gray uppercase, small size, padding-top spacing, opacity ~0.6) to match the mockup screenshot style.
  - Add optional collapsed-sidebar rule (NF4) — min-width 72px, hide labels, keep icons only.

### Test Requirements
| TR | Type | Condition |
|---|---|---|
| TR3.1 | rule | Sidebar contains 4 group labels (WORKSPACE, AI & PREDICTIVE, DATA MANAGEMENT, MANAGEMENT). |
| TR3.2 | rule | Clicking any of the original 7 nav items produces pixel-level-same page content as baseline; no refactors touched original view blocks. |
| TR3.3 | rule | Clicking each NEW nav item switches `activeView` state correctly and falls through to its case in renderView (no "not found" blank for any new item). |
| TR3.4 | rule | @media <=1024px sidebar is still readable; no horizontal scroll appears at 768px. |

---

## Task 4: Frontend — New WORKSPACE pages (Profitability, Products, Customer Intelligence, Geographic)

**Priority**: medium
**Status**: pending
**Parent ACs**: AC3, AC11, AC10

### Scope
In `App.jsx`, add 4 new view cases inside `renderView()`, each a distinct `<div className="content-grid">` with panel structure:

1. **profitability** view:
   - KPI strip: Total Profit, Profit Margin %, Return Impact, Avg Profit/Order.
   - `Bar` chart: profit by category (reuse segments/categories data → profit field).
   - `Line` chart: monthly profit trend (trend API with profit field).
   - Heatmap matrix: category × region profit intensity (reuse category_region_matrix).
   - 2 ranked panels: Top 10 profitable products; Top 10 profitable customers.

2. **products** (Product Analytics):
   - Top products table (top_products API).
   - Product count by category (Pie).
   - Product return rate (bar, synthetic — quantity × 0.3 margin / sales — or use return-pct fields).
   - Units sold × Sales scatter-style (bubble chart approach with bar chart if Chart.js scatter difficult).

3. **customers2** (Customer Intelligence — renamed key to avoid collision with original `customers`; sidebar shows "Customer Intelligence", maps to key `custintel`):
   - Top customers table (top_customers API).
   - AOV × Segment bar.
   - Repeat Customer Rate KPI.
   - Segments donut (Customer Mix from segments API).

4. **geographic** (Geographic Analysis):
   - Regions ranked table (segments/regions API).
   - Top cities bar chart (segments/cities → top 15).
   - Category × Region intensity heatmap (segments/matrix API).
   - Top-K city KPI cards row.

**Critical safety rule**: These new cases must NOT share any variables or mutate existing state for `dashboard`, `segments`, `salesRecords`; they should use fresh local `useMemo` per-view transforms or re-use the existing data safely.

### Test Requirements
| TR | Type | Condition |
|---|---|---|
| TR4.1 | rule | All 4 new pages load without console errors; blank panels or "undefined" text nowhere visible. |
| TR4.2 | rule | Profitability page contains >= 4 KPI boxes + 2 charts + heatmap + 2 top lists (≥ 8 visualizations total). |
| TR4.3 | rubric | Per-page richness and "BI feel" — scale 0–2, **pass threshold ≥ 1**. Anchors same as AC11. |

---

## Task 5: Frontend — AI & Predictive pages (Forecast enhanced w/ XGB compare, Anomalies, AI Advisor, Customer Predictions)

**Priority**: high
**Status**: pending
**Parent ACs**: AC3, AC4, AC6, AC11

### Scope

1. **forecast** key → Sales Forecast enhancement:
   - Move existing forecast UI from wherever it currently lives into this dedicated page.
   - Add model selector: `<button-group>` RandomForest / XGBoost / Compare.
   - Call `/api/sales/daily/forecast?model=rf|xgb` or `/forecast-compare`.
   - Compare mode renders two line charts side-by-side, plus a MAE/R² comparison card.

2. **anomalies** → Anomaly Detection:
   - Line chart with revenue, upper band, lower band.
   - Anomaly days rendered as red scatter-point overlay.
   - Cards grid: top 5 anomalies (date, deviation %, z-score).
   - Filter region/category/year apply to the anomalies API.

3. **advisor** → AI Business Advisor:
   - AI-style card grid: each insight from `/api/ai/advisor`.
   - Insight `type = strength/weakness/risk/opportunity` maps to colour (green, red, amber, purple).
   - Actionable recommendation button per card (just visual; sets status message).
   - Top KPI summary orb section with overall score.

4. **cust_prediction** → Customer Prediction page:
   - Call `/api/analytics/customer-predictions?top_n=50`.
   - Tier badges (High Value / At Risk / Growing) styled as coloured pills.
   - 4 KPIs: Predicted Total Revenue (sum), High Value count, At-Risk count, Avg LTV.
   - Bar chart: Top-10 customers by predicted next-value.

### Test Requirements
| TR | Type | Condition |
|---|---|---|
| TR5.1 | rule | Forecast page renders model selector with 3 options (RandomForest, XGBoost, Compare); Compare option calls `/forecast-compare` and shows MAE badges. |
| TR5.2 | rule | If xgboost not installed, Forecast page shows warning helper badge but doesn't crash. |
| TR5.3 | rule | Anomalies line chart shows band area + anomaly points without JS console errors. |
| TR5.4 | rule | AI Advisor page shows >= 5 insight cards; each contains title, detail, severity color. |
| TR5.5 | rubric | AI-feel of the 4 pages (scale 0–2); **pass ≥ 1**. Anchors: 0 = no AI aesthetics, 1 = feels like a modern AI BI product, 2 = polished, animated, professional. |

---

## Task 6: Frontend — Data Management (Database, Export/Reports) + move Import/Quality into group

**Priority**: medium
**Status**: pending
**Parent ACs**: AC3, AC7, AC11

### Scope

1. **database** view:
   - DB connection status card (green/amber from /health).
   - Bar chart: row counts per table from `/api/database/status`.
   - CSV-vs-DB parity card: CSV rows, DB order rows, difference count, green/red badge.
   - **Sync Now** button → `POST /api/database/sync`; shows spinner during sync, success toast with counts.

2. **dataimport** view:
   - Move the existing Data Control Center panel logic here (current upload card). Do not duplicate; refactor into a re-used component. Keep original quality page also as-is.

3. **quality**: existing page, unchanged — just now rendered under DATA MANAGEMENT section.

4. **export** view:
   - 4 export buttons: Sales Records CSV, Top Products CSV, Top Customers CSV, Daily Sales CSV.
   - Each calls corresponding GET endpoint, downloads via Blob + `<a>` click.
   - "Generate Full Report" button downloads zipped or concatenated CSV with timestamp in filename.

### Test Requirements
| TR | Type | Condition |
|---|---|---|
| TR6.1 | rule | Database page calls `/api/database/status` and renders row counts for ≥ 8 tables. |
| TR6.2 | rule | "Sync CSV → DB" button triggers an async call; status feedback shown; success/error banner appears. |
| TR6.3 | rule | Clicking any Export button produces a file download in the browser (may use Cypress/Playwright-level check; acceptable evidence: `window.URL.createObjectURL` call visible in DevTools Network). |

---

## Task 7: Frontend — Management pages (Audit Logs, Users & Roles, Settings)

**Priority**: low
**Status**: pending
**Parent ACs**: AC3, NF5

### Scope

1. **audit** view (Audit Logs):
   - Appends log entries into `localStorage['nexus_audit']` whenever the user performs these actions: login, logout, refresh data, upload CSV, create/update/delete sale record, sync database.
   - Render log as a table: timestamp | actor email | action | status.
   - Button to clear audit log (Admin-only).

2. **users** view (Users & Roles):
   - Fetch from `/api/management/users` (Admin) or shows a demo card for non-Admin.
   - Role-coloured badges: Admin = purple, Business Manager = blue, Analyst = teal, Viewer = gray.
   - KPI card: total users, per-role counts.

3. **settings** view:
   - Theme toggle (default dark; switch to light alternative — use CSS variable flip, minimal effort, default unchanged so existing dark style persists).
   - Default forecast horizon dropdown (1/7/14/30 days; persists in localStorage).
   - Info cards: dataset path, DB backend, app secret indicator (masked).

### Test Requirements
| TR | Type | Condition |
|---|---|---|
| TR7.1 | rule | Audit log captures login action; entry appears in table. |
| TR7.2 | rule | Users page shows role badges with correct colors. |
| TR7.3 | rule | Settings page theme toggle flips a CSS class; reverts on reload to default dark (localStorage key optional; default persistence acceptable). |

---

## Task 8: Integration smoke tests + build check

**Priority**: high
**Status**: pending
**Parent ACs**: NF1, NF2, NF3, NF5, AC9

### Scope
- Run `python -m pytest tests/test_api.py` (existing tests) → all must pass.
- Run `python -m py_compile backend/app/*.py` → 0 errors.
- Run frontend build (optional if node installed) OR at least syntax-check via node if available.
- Install xgboost (`pip install xgboost>=2.0,<3`) OR verify graceful degradation with `backend starts` both scenarios.
- Browser-side manual checklist (if backend+frontend running): login → click all 18+ sidebar items → no console errors.

### Test Requirements
| TR | Type | Condition |
|---|---|---|
| TR8.1 | rule | All existing `pytest` tests pass (must not break any existing endpoints). |
| TR8.2 | rule | Python compile passes for all modified backend files. |
| TR8.3 | rule | Backend starts with and without xgboost installed. |
| TR8.4 | rule | Manual: Demo Admin login → upload (already role-gated) → still 403 for Viewer. |
| TR8.5 | rubric | Test completeness / manual steps documented (scale 0–2; pass ≥ 1). |
