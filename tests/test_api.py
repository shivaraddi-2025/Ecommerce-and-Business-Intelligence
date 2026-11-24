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
    token = main.token_for("admin-filter@example.com", "Admin")

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


def test_uploaded_dataset_refreshes_runtime_engine(tmp_path: Path, monkeypatch) -> None:
    columns = [
        "order_id",
        "order_date",
        "order_datetime",
        "day_of_week",
        "month",
        "year",
        "customer_id",
        "customer_segment",
        "product_category",
        "product_name",
        "quantity",
        "net_amount",
        "region",
        "city",
        "order_status",
    ]
    existing = {
        "order_id": "existing-1",
        "order_date": "2026-01-01",
        "customer_id": "customer-1",
        "customer_segment": "Regular",
        "product_category": "Existing Category",
        "product_name": "Existing Product",
        "quantity": 1,
        "net_amount": 100,
        "region": "North",
        "city": "Delhi",
        "order_status": "Delivered",
    }
    active_dataset = tmp_path / "initial.csv"
    source = tmp_path / "uploaded.csv"
    main.pd.DataFrame([existing], columns=columns).to_csv(active_dataset, index=False)
    main.pd.DataFrame(
        [{**existing, "order_id": "imported-1", "net_amount": 200}],
        columns=columns,
    ).to_csv(source, index=False)
    canonical_dataset = tmp_path / "ecommerce_sales_raw.csv.csv"
    readme = tmp_path / "README.md"
    readme.write_text(
        f"Dataset details\n{main.README_DATASET_START}\ninitial status\n{main.README_DATASET_END}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATASET", active_dataset)
    monkeypatch.setattr(main, "CANONICAL_DATASET", canonical_dataset)
    monkeypatch.setattr(main, "README_PATH", readme)
    monkeypatch.setattr(main, "ACTIVE_DATASET_FILE", tmp_path / ".active_dataset_path.txt")
    monkeypatch.setattr(main, "engine", main.AnalyticsEngine(active_dataset))
    monkeypatch.setattr(main, "_archive_active_dataset", lambda: None)
    monkeypatch.setattr(main.db_sync, "sync_csv_to_db", lambda *args, **kwargs: {})
    monkeypatch.setenv("DATASET_PATH", str(active_dataset))

    token = main.token_for("admin-upload@example.com", "Admin")

    uploaded_filename = "uploaded_ecommerce_sales_raw.csv.csv"
    response = client.post(
        "/api/data/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (uploaded_filename, source.read_bytes(), "text/csv")},
        data={"mode": "append"},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == uploaded_filename
    assert main.DATASET == canonical_dataset
    assert main.pd.read_csv(canonical_dataset)["order_id"].tolist() == ["existing-1", "imported-1"]
    assert len(main.engine.frame) == 2
    assert response.json()["readme_updated"] is True
    assert "**Records**: 2" in readme.read_text(encoding="utf-8")

    replacement = {**existing, "order_id": "replacement-1", "net_amount": 400}
    replace_response = client.post(
        "/api/data/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "replacement.csv",
                main.pd.DataFrame([replacement], columns=columns).to_csv(index=False).encode(),
                "text/csv",
            )
        },
        data={"mode": "replace"},
    )
    assert replace_response.status_code == 200
    assert main.pd.read_csv(canonical_dataset)["order_id"].tolist() == ["replacement-1"]
    assert replace_response.json()["readme_updated"] is True
    assert "**Records**: 1" in readme.read_text(encoding="utf-8")


def test_resolve_dataset_path_prefers_canonical_csv(tmp_path: Path, monkeypatch) -> None:
    default_dataset = tmp_path / "default.csv"
    default_dataset.write_text("order_id\noriginal\n", encoding="utf-8")
    uploaded_dataset = tmp_path / "uploads" / "uploaded.csv"
    uploaded_dataset.parent.mkdir()
    uploaded_dataset.write_text("order_id\nimported\n", encoding="utf-8")
    canonical_dataset = tmp_path / "ecommerce_sales_raw.csv.csv"
    canonical_dataset.write_text("order_id\ncanonical\n", encoding="utf-8")
    active_dataset_file = tmp_path / ".active_dataset_path.txt"
    active_dataset_file.write_text(str(uploaded_dataset), encoding="utf-8")

    monkeypatch.setattr(main, "CANONICAL_DATASET", canonical_dataset)
    monkeypatch.setattr(main, "ACTIVE_DATASET_FILE", active_dataset_file)
    monkeypatch.setattr(main, "LARGE_DATASET", tmp_path / "missing-large.csv")
    monkeypatch.setattr(main, "DEFAULT_DATASET", default_dataset)
    monkeypatch.setenv("DATASET_PATH", str(default_dataset))

    assert main.resolve_dataset_path() == canonical_dataset


def test_individual_sale_changes_persist_to_canonical_csv(tmp_path: Path, monkeypatch) -> None:
    columns = [
        "order_id",
        "order_date",
        "order_datetime",
        "day_of_week",
        "month",
        "year",
        "customer_id",
        "customer_segment",
        "product_category",
        "product_name",
        "quantity",
        "unit_price",
        "gross_amount",
        "discount_pct",
        "discount_amount",
        "net_amount",
        "payment_method",
        "region",
        "city",
        "order_status",
    ]
    initial_row = {
        "order_id": "initial-order",
        "order_date": "2026-01-01",
        "order_datetime": "2026-01-01 10:00:00",
        "day_of_week": "Thursday",
        "month": "January",
        "year": 2026,
        "customer_id": "customer-1",
        "customer_segment": "Regular",
        "product_category": "Existing",
        "product_name": "Existing Product",
        "quantity": 1,
        "unit_price": 100,
        "gross_amount": 100,
        "discount_pct": 0,
        "discount_amount": 0,
        "net_amount": 100,
        "payment_method": "Credit Card",
        "region": "North",
        "city": "Delhi",
        "order_status": "Delivered",
    }
    canonical_dataset = tmp_path / "ecommerce_sales_raw.csv.csv"
    main.pd.DataFrame([initial_row], columns=columns).to_csv(canonical_dataset, index=False)
    readme = tmp_path / "README.md"
    readme.write_text(
        f"Dataset details\n{main.README_DATASET_START}\ninitial status\n{main.README_DATASET_END}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "CANONICAL_DATASET", canonical_dataset)
    monkeypatch.setattr(main, "DATASET", canonical_dataset)
    monkeypatch.setattr(main, "README_PATH", readme)
    monkeypatch.setattr(main, "engine", main.AnalyticsEngine(canonical_dataset))
    monkeypatch.setattr(main.db_sync, "upsert_sale_to_db", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main.db_sync, "delete_sale_from_db", lambda *_args, **_kwargs: None)

    with canonical_dataset.open("rb+") as dataset_file:
        dataset_file.seek(-1, 2)
        assert dataset_file.read(1) == b"\n"
        dataset_file.truncate(dataset_file.tell() - 1)

    token = main.token_for("canonical-sales-admin@example.com", "Admin")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/sales/records",
        headers=headers,
        json={
            "order_id": "new-order",
            "order_date": "2026-01-02",
            "customer_id": "customer-2",
            "product_name": "New Product",
            "product_category": "New Category",
            "quantity": 2,
            "unit_price": 50,
            "region": "North",
            "city": "Delhi",
        },
    )
    assert created.status_code == 200
    after_create = main.pd.read_csv(canonical_dataset)
    assert "new-order" in after_create["order_id"].tolist()
    assert created.json()["readme_updated"] is True

    updated = client.put(
        "/api/sales/records/new-order",
        headers=headers,
        json={"product_name": "Updated Product", "sales": 175},
    )
    assert updated.status_code == 200
    after_update = main.pd.read_csv(canonical_dataset)
    updated_row = after_update.loc[after_update["order_id"].eq("new-order")].iloc[0]
    assert updated_row["product_name"] == "Updated Product"
    assert updated_row["net_amount"] == 175

    deleted = client.delete("/api/sales/records/new-order", headers=headers)
    assert deleted.status_code == 200
    assert "new-order" not in main.pd.read_csv(canonical_dataset)["order_id"].tolist()


def test_restoring_version_writes_canonical_dataset_and_readme(tmp_path: Path, monkeypatch) -> None:
    columns = [
        "order_id",
        "order_date",
        "customer_id",
        "customer_segment",
        "product_category",
        "product_name",
        "quantity",
        "net_amount",
        "region",
        "city",
        "order_status",
    ]
    row = {
        "order_id": "restored-1",
        "order_date": "2026-01-01",
        "customer_id": "customer-1",
        "customer_segment": "Regular",
        "product_category": "Restored Category",
        "product_name": "Restored Product",
        "quantity": 1,
        "net_amount": 125,
        "region": "North",
        "city": "Delhi",
        "order_status": "Delivered",
    }
    versions_dir = tmp_path / "versions"
    versions_dir.mkdir()
    version_id = "a" * 32
    version_path = versions_dir / f"{version_id}.csv"
    main.pd.DataFrame([row], columns=columns).to_csv(version_path, index=False)
    active_dataset = tmp_path / "active.csv"
    main.pd.DataFrame([{**row, "order_id": "old-1"}], columns=columns).to_csv(active_dataset, index=False)
    canonical_dataset = tmp_path / "ecommerce_sales_raw.csv.csv"
    readme = tmp_path / "README.md"
    readme.write_text(
        f"Dataset details\n{main.README_DATASET_START}\ninitial status\n{main.README_DATASET_END}\n",
        encoding="utf-8",
    )
    active_path_file = tmp_path / ".active_dataset_path.txt"
    monkeypatch.setattr(main, "DATASET", active_dataset)
    monkeypatch.setattr(main, "CANONICAL_DATASET", canonical_dataset)
    monkeypatch.setattr(main, "DATASET_VERSIONS_DIR", versions_dir)
    monkeypatch.setattr(main, "ACTIVE_DATASET_FILE", active_path_file)
    monkeypatch.setattr(main, "README_PATH", readme)
    monkeypatch.setattr(main, "engine", main.AnalyticsEngine(active_dataset))
    monkeypatch.setattr(main, "_archive_active_dataset", lambda: None)
    monkeypatch.setattr(main.db_sync, "sync_csv_to_db", lambda *args, **kwargs: {})

    token = main.token_for("restore-admin@example.com", "Admin")
    response = client.post(
        f"/api/data/restore/{version_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert main.DATASET == canonical_dataset
    assert active_path_file.read_text(encoding="utf-8") == str(canonical_dataset)
    assert main.pd.read_csv(canonical_dataset)["order_id"].tolist() == ["restored-1"]
    assert response.json()["readme_updated"] is True
    assert "**Records**: 1" in readme.read_text(encoding="utf-8")


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


def test_registration_cannot_assign_an_elevated_role() -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "self-assigned-admin@example.com", "password": "long-password", "role": "Admin"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "Viewer"


def test_admin_assigns_manager_branch_and_manager_data_is_scoped() -> None:
    region = main.engine.regions[0]
    city = main.engine.get_cities(region)[0]
    other_city = next(value for value in main.engine.get_cities(region) if value != city)
    admin_headers = {"Authorization": f"Bearer {main.token_for('branch-admin@example.com', 'Admin')}"}
    region_assignment = client.post(
        "/api/management/users/invite",
        json={"email": "region-only-manager@example.com", "password": "temporary-password", "role": "Manager", "branch": region},
        headers=admin_headers,
    )
    assert region_assignment.status_code == 400

    invite = client.post(
        "/api/management/users/invite",
        json={"email": "branch-manager@example.com", "password": "temporary-password", "role": "Manager", "branch": city},
        headers=admin_headers,
    )
    assert invite.status_code == 200
    assert invite.json()["branch"] == city
    assert invite.json()["branch_city"] == city
    assert invite.json()["branch_region"] == region

    login = client.post(
        "/api/auth/login",
        json={"email": "branch-manager@example.com", "password": "temporary-password"},
    )
    assert login.status_code == 200
    assert login.json()["branch"] == city
    assert login.json()["city"] == city
    assert login.json()["region"] == region
    manager_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    dashboard = client.get(f"/api/dashboard/kpis?region=not-your-branch&city={other_city}", headers=manager_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["filters"]["regions"] == [region]
    assert dashboard.json()["filters"]["cities"] == [city]
    assert dashboard.json()["filters"]["city_regions"] == {city: region}
    assert dashboard.json()["kpis"] == main.engine.kpis(region=region, city=city)
    scoped_records = client.get(f"/api/sales/records?region=not-your-branch&city={other_city}&limit=5", headers=manager_headers)
    assert scoped_records.status_code == 200
    assert all(record["city"] == city and record["region"] == region for record in scoped_records.json()["records"])
    scoped_cities = client.get(f"/api/segments/cities?city={other_city}", headers=manager_headers)
    assert scoped_cities.status_code == 200
    assert {row["City"] for row in scoped_cities.json()["rows"]} == {city}

    users = client.get("/api/management/users", headers=manager_headers)
    assert users.status_code == 403
    create_sale = client.post(
        "/api/sales/records",
        json={"product_name": "Denied", "product_category": "Test", "unit_price": 1, "region": region, "city": city},
        headers=manager_headers,
    )
    assert create_sale.status_code == 403
    other_record = main.engine.get_sales_records(region=region, city=other_city, limit=1)["records"][0]
    delete_other_city = client.delete(
        f"/api/sales/records/{other_record['order_id']}",
        headers=manager_headers,
    )
    assert delete_other_city.status_code == 404


def test_manager_replace_preserves_other_branches(tmp_path: Path, monkeypatch) -> None:
    active_dataset = main.DATASET
    region = main.engine.regions[0]
    city = main.engine.get_cities(region)[0]
    original = main.pd.read_csv(active_dataset)
    row = original.loc[original["city"].astype(str).str.casefold() == city.casefold()].iloc[[0]].copy()
    row.loc[:, "order_id"] = "manager-replacement-test"
    upload_content = row.to_csv(index=False).encode("utf-8")
    other_city_counts = original.loc[
        original["city"].astype(str).str.casefold() != city.casefold(), "city"
    ].value_counts().to_dict()

    activated: dict[str, Path] = {}

    def activate_dataset(path: Path, dataset_engine) -> None:
        activated["path"] = path
        monkeypatch.setattr(main, "DATASET", path)
        monkeypatch.setattr(main, "engine", dataset_engine)

    monkeypatch.setattr(main, "DATASET", active_dataset)
    monkeypatch.setattr(main, "CANONICAL_DATASET", tmp_path / "ecommerce_sales_raw.csv.csv")
    readme = tmp_path / "README.md"
    readme.write_text(
        f"Dataset details\n{main.README_DATASET_START}\ninitial status\n{main.README_DATASET_END}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "README_PATH", readme)
    monkeypatch.setattr(main, "_archive_active_dataset", lambda: None)
    monkeypatch.setattr(main, "_activate_dataset", activate_dataset)
    monkeypatch.setattr(main.db_sync, "sync_csv_to_db", lambda *args, **kwargs: {})

    manager_token = main.token_for("upload-branch-manager@example.com", "Manager", city)
    response = client.post(
        "/api/data/upload",
        headers={"Authorization": f"Bearer {manager_token}"},
        files={"file": ("branch.csv", upload_content, "text/csv")},
        data={"mode": "replace"},
    )
    assert response.status_code == 200
    replaced = main.pd.read_csv(activated["path"])
    replaced_cities = replaced["city"].astype(str).str.casefold()
    assert int(replaced_cities.eq(city.casefold()).sum()) == 1
    assert replaced.loc[replaced_cities.eq(city.casefold()), "order_id"].iloc[0] == "manager-replacement-test"
    actual_other_city_counts = replaced.loc[~replaced_cities.eq(city.casefold()), "city"].value_counts().to_dict()
    assert actual_other_city_counts == other_city_counts


def test_manager_upload_cannot_include_other_branches() -> None:
    region = main.engine.regions[0]
    city = main.engine.get_cities(region)[0]
    other_city = next(value for value in main.engine.get_cities(region) if value != city)
    manager_token = main.token_for("upload-other-branch@example.com", "Manager", city)
    response = client.post(
        "/api/data/upload",
        headers={"Authorization": f"Bearer {manager_token}"},
        files={"file": ("branch.csv", f"order_id,city,region\nA-1,{other_city},{region}\n".encode(), "text/csv")},
        data={"mode": "append"},
    )

    assert response.status_code == 403


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


def test_viewer_cannot_create_update_delete_or_refresh_sales() -> None:
    viewer_token = main.token_for("sales-viewer@example.com", "Viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}
    sale = {
        "product_name": "Viewer permission test",
        "product_category": "Test",
        "unit_price": 10,
        "region": "Test",
        "city": "Test",
    }

    create = client.post("/api/sales/records", json=sale, headers=headers)
    update = client.put("/api/sales/records/VIEWER-TEST", json={"product_name": "Changed"}, headers=headers)
    delete = client.delete("/api/sales/records/VIEWER-TEST", headers=headers)
    refresh = client.post("/api/sales/refresh", headers=headers)

    assert create.status_code == 403
    assert update.status_code == 403
    assert delete.status_code == 403
    assert refresh.status_code == 403


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