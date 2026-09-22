from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .analytics import AnalyticsEngine


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "data" / "raw" / "ecommerce_sales_raw.csv"
LARGE_DATASET = ROOT / "data" / "raw" / "ecommerce_sales_raw.csv.csv"
ACTIVE_DATASET_FILE = ROOT / "data" / "raw" / ".active_dataset_path.txt"


def resolve_dataset_path() -> Path:
    env_dataset = os.getenv("DATASET_PATH")
    if env_dataset:
        candidate = Path(env_dataset)
        if candidate.exists():
            return candidate

    if ACTIVE_DATASET_FILE.exists():
        stored = ACTIVE_DATASET_FILE.read_text().strip()
        if stored:
            candidate = Path(stored)
            if candidate.exists():
                return candidate

    if LARGE_DATASET.exists():
        return LARGE_DATASET

    if DEFAULT_DATASET.exists():
        return DEFAULT_DATASET

    return Path(r"C:\Users\shiva\Downloads\data analytics project\ecommerce_sales_raw.csv")


DATASET = resolve_dataset_path()

app = FastAPI(title="Nexus Commerce Intelligence API", version="1.0.0")
security = HTTPBearer(auto_error=False)
engine = AnalyticsEngine(DATASET)
users: dict[str, dict[str, str]] = {}


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return base64.b64encode(salt + digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    raw = base64.b64decode(encoded.encode())
    return hmac.compare_digest(hash_password(password, raw[:16]), encoded)


users["demo@example.com"] = {
    "password": hash_password("demo-password"),
    "role": "Admin",
}


def token_for(email: str, role: str) -> str:
    secret = os.getenv("APP_SECRET", "local-development-secret").encode()
    payload = {"sub": email, "role": role, "exp": int((datetime.now(timezone.utc) + timedelta(hours=8)).timestamp())}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict[str, str]:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        body, signature = credentials.credentials.split(".")
        secret = os.getenv("APP_SECRET", "local-development-secret").encode()
        if not hmac.compare_digest(hmac.new(secret, body.encode(), hashlib.sha256).hexdigest(), signature):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        if payload["exp"] < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError
        return payload
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    role: str = "Viewer"


class LoginRequest(BaseModel):
    email: str
    password: str


class FilterOptionsRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class PredictionRequest(BaseModel):
    quantity: int = Field(gt=0, le=10000)
    sales: float = Field(gt=0)
    discount: float = Field(ge=0, le=1)
    category: str
    region: str


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"status": "ok", "dataset": DATASET.name, "records": len(engine.frame)}


@app.post("/api/auth/register")
def register(request: RegisterRequest) -> dict[str, str]:
    if request.email in users:
        raise HTTPException(status_code=409, detail="User already exists")
    role = request.role if request.role in {"Admin", "Business Manager", "Analyst", "Viewer"} else "Viewer"
    users[request.email] = {"password": hash_password(request.password), "role": role}
    return {"access_token": token_for(request.email, role), "token_type": "bearer", "role": role}


@app.post("/api/auth/login")
def login(request: LoginRequest) -> dict[str, str]:
    user = users.get(request.email)
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": token_for(request.email, user["role"]), "token_type": "bearer", "role": user["role"]}


@app.get("/api/dashboard/kpis")
def dashboard_kpis(region: str | None = None, category: str | None = None, year: str | None = None, city: str | None = None, user: dict[str, str] = Depends(current_user)) -> dict[str, object]:
    return {"kpis": engine.kpis(region, category, year, city), "filters": {"regions": engine.regions, "categories": engine.categories, "cities": engine.cities}}


@app.get("/api/sales/trend")
def sales_trend(region: str | None = None, category: str | None = None, year: str | None = None, city: str | None = None, user: dict[str, str] = Depends(current_user)) -> list[dict[str, object]]:
    return engine.trend(region, category, year, city)


@app.get("/api/sales/daily")
def sales_daily(region: str | None = None, category: str | None = None, year: str | None = None, city: str | None = None, user: dict[str, str] = Depends(current_user)) -> list[dict[str, object]]:
    return engine.daily_trend(region, category, year, city)


@app.get("/api/sales/daily/report")
def sales_daily_report(region: str | None = None, category: str | None = None, year: str | None = None, city: str | None = None, user: dict[str, str] = Depends(current_user)) -> dict[str, object]:
    return engine.daily_performance_report(region, category, year, city)


@app.get("/api/sales/daily/forecast")
def sales_daily_forecast(date: str | None = None, year: str | None = None, user: dict[str, str] = Depends(current_user)) -> dict[str, object]:
    return engine.forecast_daily_sales(date, year)


@app.get("/api/sales/category")
def sales_category(user: dict[str, str] = Depends(current_user)) -> list[dict[str, object]]:
    return engine.category_performance()


@app.get("/api/products/top")
def products_top(user: dict[str, str] = Depends(current_user)) -> list[dict[str, object]]:
    return engine.top_products()


@app.get("/api/customers/top")
def customers_top(user: dict[str, str] = Depends(current_user)) -> list[dict[str, object]]:
    return engine.customers()


@app.get("/api/recommendations")
def recommendations(customer_id: str | None = None, user: dict[str, str] = Depends(current_user)) -> list[dict[str, object]]:
    return engine.recommendations(customer_id)


@app.post("/api/admin/regions")
def add_region(request: FilterOptionsRequest, user: dict[str, str] = Depends(current_user)) -> dict[str, str]:
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    try:
        value = engine.add_region(request.name)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "added", "name": value}


@app.delete("/api/admin/regions/{name}")
def delete_region(name: str, user: dict[str, str] = Depends(current_user)) -> dict[str, str]:
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    try:
        deleted = engine.delete_region(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "deleted", "name": deleted}


@app.post("/api/admin/categories")
def add_category(request: FilterOptionsRequest, user: dict[str, str] = Depends(current_user)) -> dict[str, str]:
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    try:
        value = engine.add_category(request.name)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "added", "name": value}


@app.delete("/api/admin/categories/{name}")
def delete_category(name: str, user: dict[str, str] = Depends(current_user)) -> dict[str, str]:
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    try:
        deleted = engine.delete_category(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "deleted", "name": deleted}


@app.get("/api/data/quality")
def data_quality(user: dict[str, str] = Depends(current_user)) -> dict[str, object]:
    return engine.quality()


@app.post("/api/predict")
def predict(request: PredictionRequest, user: dict[str, str] = Depends(current_user)) -> dict[str, object]:
    if request.category not in engine.categories or request.region not in engine.regions:
        raise HTTPException(status_code=422, detail="Category or region is not present in the dataset")
    return engine.predict(request.quantity, request.sales, request.discount, request.category, request.region)


@app.post("/api/data/upload")
async def upload_dataset(file: UploadFile = File(...), user: dict[str, str] = Depends(current_user)) -> dict[str, str]:
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")

    global DATASET, engine

    target = ROOT / "data" / "raw" / file.filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(await file.read())

    DATASET = target
    os.environ["DATASET_PATH"] = str(target)
    ACTIVE_DATASET_FILE.write_text(str(target))
    engine = AnalyticsEngine(DATASET)

    return {"status": "uploaded", "filename": file.filename}