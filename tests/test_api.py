from pathlib import Path

from fastapi.testclient import TestClient

import backend.app.main as main
from backend.app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["records"] >= 80000


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
    assert dashboard.json()["kpis"]["orders"] >= 80000


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
    assert len(main.engine.frame) >= 80000


def test_demo_user_can_login() -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@example.com", "password": "demo-password"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "Admin"
    assert payload["access_token"].startswith("eyJ")


def test_admin_can_invite_user_who_can_sign_in() -> None:
    admin_token = main.token_for("invite-admin@example.com", "Admin")
    email = "new-invite@example.com"
    response = client.post(
        "/api/management/users/invite",
        json={"email": email, "password": "temporary-password", "role": "Analyst"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == email
    assert response.json()["role"] == "Analyst"

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "temporary-password"},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "Analyst"


def test_business_manager_cannot_invite_admin() -> None:
    manager_token = main.token_for("invite-manager@example.com", "Business Manager")
    response = client.post(
        "/api/management/users/invite",
        json={"email": "new-admin-invite@example.com", "password": "temporary-password", "role": "Admin"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 403


def test_viewer_cannot_invite_user() -> None:
    viewer_token = main.token_for("invite-viewer@example.com", "Viewer")
    response = client.post(
        "/api/management/users/invite",
        json={"email": "forbidden-invite@example.com", "password": "temporary-password", "role": "Viewer"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


def test_registration_stores_scrypt_password_hash() -> None:
    email = "password-hash@example.com"
    password = "registration-password"
    response = client.post("/api/auth/register", json={"email": email, "password": password})

    assert response.status_code == 200
    with main.get_session() as session:
        user = main.get_user_by_email(session, email)
        assert user is not None
        assert user.password.startswith("scrypt$")
        assert user.password != password
        assert main.verify_password(password, user.password)


def test_login_upgrades_legacy_plaintext_password() -> None:
    email = "legacy-password@example.com"
    password = "legacy-password"
    with main.get_session() as session:
        main.create_user(session, email, password, role="Viewer")

    response = client.post("/api/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200
    with main.get_session() as session:
        user = main.get_user_by_email(session, email)
        assert user is not None
        assert user.password.startswith("scrypt$")
        assert user.password != password
        assert main.verify_password(password, user.password)


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
    assert any(term in payload["basis"].lower() for term in ["moving", "random forest", "average"])
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
    assert any(term in payload["basis"].lower() for term in ["moving", "random forest", "average"])
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