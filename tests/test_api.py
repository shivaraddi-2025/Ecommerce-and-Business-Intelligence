from pathlib import Path

from fastapi.testclient import TestClient

import backend.app.main as main
from backend.app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["records"] == 80000


def test_protected_dashboard_requires_login() -> None:
    response = client.get("/api/dashboard/kpis")
    assert response.status_code == 401


def test_register_and_dashboard() -> None:
    email = "test-api@example.com"
    response = client.post("/api/auth/register", json={"email": email, "password": "long-password"})
    assert response.status_code in {200, 409}
    token = response.json().get("access_token") if response.status_code == 200 else client.post("/api/auth/login", json={"email": email, "password": "long-password"}).json()["access_token"]
    dashboard = client.get("/api/dashboard/kpis", headers={"Authorization": f"Bearer {token}"})
    assert dashboard.status_code == 200
    assert dashboard.json()["kpis"]["orders"] == 80000


def test_admin_can_manage_filter_options() -> None:
    email = "admin-filter@example.com"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "long-password", "role": "Admin"},
    )
    assert register.status_code in {200, 409}
    token = register.json().get("access_token") if register.status_code == 200 else client.post(
        "/api/auth/login",
        json={"email": email, "password": "long-password"},
    ).json()["access_token"]

    add_region = client.post(
        "/api/admin/regions",
        json={"name": "Atlantis"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_region.status_code == 200

    add_category = client.post(
        "/api/admin/categories",
        json={"name": "Home Care"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_category.status_code == 200

    dashboard = client.get("/api/dashboard/kpis", headers={"Authorization": f"Bearer {token}"})
    assert dashboard.status_code == 200
    assert "Atlantis" in dashboard.json()["filters"]["regions"]
    assert "Home Care" in dashboard.json()["filters"]["categories"]

    delete_region = client.delete(
        "/api/admin/regions/Atlantis",
        headers={"Authorization": f"Bearer {token}"},
    )
    delete_category = client.delete(
        "/api/admin/categories/Home%20Care",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_region.status_code == 200
    assert delete_category.status_code == 200

    dashboard_again = client.get("/api/dashboard/kpis", headers={"Authorization": f"Bearer {token}"})
    assert dashboard_again.status_code == 200
    assert "Atlantis" not in dashboard_again.json()["filters"]["regions"]
    assert "Home Care" not in dashboard_again.json()["filters"]["categories"]


def test_uploaded_dataset_refreshes_runtime_engine() -> None:
    email = "admin-upload@example.com"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "long-password", "role": "Admin"},
    )
    assert register.status_code in {200, 409}
    token = register.json().get("access_token") if register.status_code == 200 else client.post(
        "/api/auth/login",
        json={"email": email, "password": "long-password"},
    ).json()["access_token"]

    source = Path("data/raw/ecommerce_sales_raw.csv.csv")
    uploaded_filename = "uploaded_ecommerce_sales_raw.csv.csv"
    response = client.post(
        "/api/data/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (uploaded_filename, source.read_bytes(), "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == uploaded_filename
    assert main.DATASET == main.ROOT / "data" / "raw" / uploaded_filename
    assert len(main.engine.frame) == 80000


def test_demo_user_can_login() -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@example.com", "password": "demo-password"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "Admin"
    assert payload["access_token"].startswith("eyJ")


def test_day_level_sales_endpoint_returns_daily_records() -> None:
    email = "daily-analysis@example.com"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "long-password", "role": "Viewer"},
    )
    assert register.status_code in {200, 409}
    token = register.json().get("access_token") if register.status_code == 200 else client.post(
        "/api/auth/login",
        json={"email": email, "password": "long-password"},
    ).json()["access_token"]

    response = client.get(
        "/api/sales/daily",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 365
    assert rows[0]["Order Date"]
    assert rows[0]["sales"] >= 0
    assert rows[0]["profit"] >= -100000
    assert rows[0]["orders"] >= 1


def test_daily_performance_report_endpoint_returns_summary_and_detailed_days() -> None:
    email = "daily-report@example.com"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "long-password", "role": "Viewer"},
    )
    assert register.status_code in {200, 409}
    token = register.json().get("access_token") if register.status_code == 200 else client.post(
        "/api/auth/login",
        json={"email": email, "password": "long-password"},
    ).json()["access_token"]

    response = client.get(
        "/api/sales/daily/report",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert "daily" in payload
    assert "top_day" in payload["summary"]
    assert "low_day" in payload["summary"]
    assert "risk_days" in payload["summary"]
    assert payload["daily"]
    assert payload["summary"]["top_day"]["Order Date"]
    assert payload["summary"]["low_day"]["Order Date"]


def test_daily_forecast_endpoint_returns_next_day_prediction() -> None:
    email = "daily-forecast@example.com"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "long-password", "role": "Viewer"},
    )
    assert register.status_code in {200, 409}
    token = register.json().get("access_token") if register.status_code == 200 else client.post(
        "/api/auth/login",
        json={"email": email, "password": "long-password"},
    ).json()["access_token"]

    response = client.get(
        "/api/sales/daily/forecast",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["forecast_date"]
    assert payload["predicted_sales"] >= 0
    assert payload["predicted_profit"] >= -100000
    assert payload["predicted_orders"] >= 1
    assert payload["confidence"] >= 0 and payload["confidence"] <= 100
    assert "moving" in payload["basis"].lower()
    assert "return_rate" in payload


def test_daily_forecast_endpoint_accepts_selected_date_and_year_filter() -> None:
    email = "daily-forecast-date-year@example.com"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "long-password", "role": "Viewer"},
    )
    assert register.status_code in {200, 409}
    token = register.json().get("access_token") if register.status_code == 200 else client.post(
        "/api/auth/login",
        json={"email": email, "password": "long-password"},
    ).json()["access_token"]

    response = client.get(
        "/api/sales/daily/forecast?date=2025-12-31&year=2025",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["forecast_date"] == "2026-01-01"
    assert payload["basis"].lower().startswith("moving")
    assert "return_rate" in payload


def test_dashboard_accepts_combined_region_and_category_filters() -> None:
    email = "combined-filter@example.com"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "long-password", "role": "Viewer"},
    )
    assert register.status_code in {200, 409}
    token = register.json().get("access_token") if register.status_code == 200 else client.post(
        "/api/auth/login",
        json={"email": email, "password": "long-password"},
    ).json()["access_token"]

    response = client.get(
        "/api/dashboard/kpis?region=North,South&category=Furniture,Office%20Supplies",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["kpis"]["sales"] >= 0
    assert payload["filters"]["regions"]
    assert payload["filters"]["categories"]