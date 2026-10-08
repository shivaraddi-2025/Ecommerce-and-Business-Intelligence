# Nexus Commerce Intelligence

A decision-support system for e-commerce analytics. It includes dataset-backed KPIs, sales forecasting, data quality metrics, role-aware authentication, product recommendations, REST APIs, and a React dashboard — all backed by 80,000 real orders.

---

## 🚀 How to Run This Project

### Prerequisites (First-Time Setup Only)

Before running the project for the first time, make sure you have installed:

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)

Then run these commands **once** from the project root (`my project` folder):

```powershell
# 1. Create Python virtual environment
python -m venv .venv

# 2. Install Python packages
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Install Node packages
npm install
```

---

### ✅ Running the Project (Every Time)

Open a terminal at `C:\Users\shiva\Downloads\my project` and run:

```powershell
npm run dev
```

This single command starts **both** the backend and frontend together.

You will see:
```
[BACKEND] Uvicorn running on http://127.0.0.1:8000
[FRONTEND] VITE ready → http://localhost:5173/
```

Then open your browser and go to:

👉 **http://localhost:5173**

---

### 🔐 Login Credentials

| Field    | Value               |
|----------|---------------------|
| Email    | demo@example.com    |
| Password | demo-password       |
| Role     | Admin               |

---

### 🌐 Available URLs

| URL                                        | Description                        |
|--------------------------------------------|------------------------------------|
| http://localhost:5173                      | React Dashboard (frontend dev mode)|
| http://127.0.0.1:8000                      | API + built dashboard              |
| http://127.0.0.1:8000/docs                 | Interactive API documentation      |
| http://127.0.0.1:8000/api/health           | Backend health check               |

---

### 📦 Other Useful Commands

| Command             | What it does                              |
|---------------------|-------------------------------------------|
| `npm run dev`       | ⭐ Start both backend + frontend together  |
| `npm run backend`   | Start only the Python backend             |
| `npm run frontend`  | Start only the React frontend             |
| `npm run build`     | Build the frontend for production         |
| `python -m pytest`  | Run all automated tests                   |

---

### ⚠️ Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ECONNREFUSED 127.0.0.1:8000` | Backend is not running | Run `npm run dev` from the project root, not from the `frontend` folder |
| `[WinError 10013] access permissions` | Port 8000 already in use | Close any other terminal that is running the backend |
| `ModuleNotFoundError: No module named 'fastapi'` | Wrong Python used | Use `.\.venv\Scripts\python.exe`, not system `python` |
| `cd my project` fails in PowerShell | Folder name has a space | Use quotes: `cd "my project"` |
| `Unable to sign in` on login page | Backend not running | Make sure backend is started before opening the browser |

---

## 📁 Project Structure

```
my project/
├── backend/
│   └── app/
│       ├── main.py         ← FastAPI routes and auth
│       └── analytics.py    ← KPI, forecasting, recommendations logic
├── frontend/
│   └── src/
│       └── App.jsx         ← React dashboard
├── data/
│   └── raw/
│       └── ecommerce_sales_raw.csv.csv  ← 80,000 orders dataset
├── tests/
│   └── test_api.py         ← Automated API tests
├── requirements.txt        ← Python dependencies
├── package.json            ← Node scripts
└── README.md               ← This file
```

---

## 📡 Included API Endpoints

| Endpoint                     | Description                     |
|------------------------------|---------------------------------|
| `GET /api/health`            | Health check                    |
| `POST /api/auth/register`    | Register new user               |
| `POST /api/auth/login`       | Login and get token             |
| `GET /api/dashboard/kpis`    | KPI summary (sales, profit etc) |
| `GET /api/sales/trend`       | Monthly sales trend             |
| `GET /api/sales/category`    | Sales by product category       |
| `GET /api/sales/daily`       | Day-level sales records         |
| `GET /api/sales/daily/report`| Daily performance report        |
| `GET /api/sales/daily/forecast` | ML sales forecast            |
| `GET /api/products/top`      | Top selling products            |
| `GET /api/customers/top`     | Top customers by revenue        |
| `GET /api/recommendations`   | Product recommendations         |
| `GET /api/data/quality`      | Dataset quality metrics         |
| `POST /api/predict`          | Revenue prediction              |
| `POST /api/data/upload`      | Upload new dataset (Admin only) |

---

## 🧪 Running Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

All 11 tests should pass.

---

## 📊 Dataset

- **File**: `data/raw/ecommerce_sales_raw.csv.csv`
- **Size**: 80,000 orders
- **Columns**: Order ID, Order Date, Customer, Product, Category, Region, City, Sales, Profit, Discount, Quantity
- **Note**: Profit is estimated at a 30% margin (no cost data in the source)