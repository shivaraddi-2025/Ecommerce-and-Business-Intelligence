from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.app.analytics import AnalyticsEngine


def test_analytics_recalculates_from_active_dataset(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    stale_daily_path = tmp_path / "data" / "raw" / "daily_sales_dataset.csv"
    stale_daily_path.parent.mkdir(parents=True)
    pd.DataFrame(
        [{"Order Date": "2020-01-01", "sales": 999999, "profit": 0, "orders": 1}]
    ).to_csv(stale_daily_path, index=False)

    active_dataset = tmp_path / "uploaded.csv"
    pd.DataFrame(
        [
            {
                "Order ID": "new-1",
                "Order Date": "2026-01-01",
                "Customer ID": "customer-1",
                "Customer Name": "Customer One",
                "Segment": "Regular",
                "Product ID": "product-1",
                "Product Name": "Product One",
                "Category": "New Category",
                "Sub-Category": "New Category",
                "Region": "North",
                "State": "Delhi",
                "City": "Delhi",
                "Quantity": 2,
                "Sales": 100,
                "Profit": 30,
                "Discount": 0,
                "Return Status": "Not Returned",
                "Shipping Mode": "Card",
            },
            {
                "Order ID": "new-2",
                "Order Date": "2026-01-01",
                "Customer ID": "customer-2",
                "Customer Name": "Customer Two",
                "Segment": "Regular",
                "Product ID": "product-2",
                "Product Name": "Product Two",
                "Category": "New Category",
                "Sub-Category": "New Category",
                "Region": "North",
                "State": "Delhi",
                "City": "Delhi",
                "Quantity": 1,
                "Sales": 200,
                "Profit": 60,
                "Discount": 0,
                "Return Status": "Not Returned",
                "Shipping Mode": "Card",
            },
        ]
    ).to_csv(active_dataset, index=False)

    engine = AnalyticsEngine(active_dataset)

    assert engine.kpis()["sales"] == 300
    assert engine.category_performance() == [
        {"Category": "New Category", "sales": 300, "profit": 90, "orders": 2, "return_rate": 0.0}
    ]
    assert engine.daily_frame["sales"].tolist() == [300]
    assert engine.daily_frame["Order Date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-01-01"]
