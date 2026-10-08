from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = [
    "Order ID",
    "Order Date",
    "Customer ID",
    "Customer Name",
    "Product ID",
    "Product Name",
    "Category",
    "Sub-Category",
    "Region",
    "State",
    "City",
    "Quantity",
    "Sales",
    "Profit",
    "Discount",
    "Shipping Mode",
    "Return Status",
]
DEFAULT_DATASET_PATH = Path(
    os.getenv(
        "DATASET_PATH",
        r"C:\Users\shiva\Downloads\data analytics project\ecommerce_sales_raw.csv",
    )
)


def numeric_profile(series: pd.Series) -> dict[str, float | int]:
    values = pd.to_numeric(series, errors="coerce")
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    outliers = (values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)
    return {
        "invalid_count": int(values.isna().sum()),
        "min": float(values.min()),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "iqr_outlier_count": int(outliers.sum()),
    }


def markdown_table(frame: pd.DataFrame, include_index: bool = False) -> str:
    table = frame.reset_index() if include_index else frame.reset_index(drop=True)
    headers = table.columns.tolist()
    lines = [
        "| " + " | ".join(str(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in table.itertuples(index=False, name=None)
    )
    return "\n".join(lines)


def profile_dataset(input_path: Path, report_dir: Path) -> None:
    frame = pd.read_csv(input_path)
    report_dir.mkdir(parents=True, exist_ok=True)

    dates = pd.to_datetime(frame["Order Date"], errors="coerce")
    quantity = pd.to_numeric(frame["Quantity"], errors="coerce")
    sales = pd.to_numeric(frame["Sales"], errors="coerce")
    profit = pd.to_numeric(frame["Profit"], errors="coerce")
    discount = pd.to_numeric(frame["Discount"], errors="coerce")

    expected_set = set(EXPECTED_COLUMNS)
    actual_set = set(frame.columns)
    quality_rows = []
    for column in frame.columns:
        values = frame[column]
        quality_rows.append(
            {
                "column": column,
                "dtype": str(values.dtype),
                "row_count": len(values),
                "missing_count": int(values.isna().sum()),
                "missing_percent": round(float(values.isna().mean() * 100), 4),
                "unique_count": int(values.nunique(dropna=False)),
                "duplicate_value_count": int(values.duplicated().sum()),
            }
        )

    quality_report = pd.DataFrame(quality_rows)
    quality_report.to_csv(report_dir / "data_quality_report.csv", index=False)

    rules = {
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "duplicate_order_ids": int(frame["Order ID"].duplicated().sum()),
        "invalid_dates": int(dates.isna().sum()),
        "nonpositive_quantity": int((quantity <= 0).sum()),
        "negative_sales": int((sales < 0).sum()),
        "negative_profit": int((profit < 0).sum()),
        "invalid_discount": int((~discount.between(0, 1) & discount.notna()).sum()),
        "invalid_return_status": int(
            (~frame["Return Status"].isin(["Returned", "Not Returned"])).sum()
        ),
        "missing_customer_name": int(frame["Customer Name"].isna().sum()),
        "inconsistent_region_case": int(
            frame["Region"].isin(frame["Region"].str.upper()).sum()
        ),
    }

    numeric = {
        column: numeric_profile(frame[column])
        for column in ["Quantity", "Sales", "Profit", "Discount"]
    }
    categorical = {
        column: frame[column].value_counts(dropna=False).to_dict()
        for column in [
            "Category",
            "Sub-Category",
            "Region",
            "Shipping Mode",
            "Return Status",
        ]
    }
    category_summary = (
        frame.groupby("Category")
        .agg(records=("Order ID", "size"), sales=("Sales", "sum"), profit=("Profit", "sum"))
        .round(2)
        .sort_values("sales", ascending=False)
    )

    summary = {
        "input_file": str(input_path),
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "expected_columns_match": actual_set == expected_set,
        "missing_expected_columns": sorted(expected_set - actual_set),
        "unexpected_columns": sorted(actual_set - expected_set),
        "columns": frame.columns.tolist(),
        "dtypes": frame.dtypes.astype(str).to_dict(),
        "date_range": {
            "min": None if dates.isna().all() else str(dates.min().date()),
            "max": None if dates.isna().all() else str(dates.max().date()),
        },
        "unique_counts": frame.nunique(dropna=False).to_dict(),
        "rules": rules,
        "numeric": numeric,
        "categorical_value_counts": categorical,
        "category_summary": category_summary.to_dict("index"),
    }
    (report_dir / "data_profile.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )

    markdown = [
        "# E-Commerce Dataset Profile",
        "",
        f"- Rows: **{summary['row_count']:,}**",
        f"- Columns: **{summary['column_count']}**",
        f"- Date range: **{summary['date_range']['min']} to {summary['date_range']['max']}**",
        f"- Expected schema match: **{summary['expected_columns_match']}**",
        "",
        "## Quality Findings",
        "",
    ]
    markdown.extend(
        f"- {name.replace('_', ' ').title()}: **{value:,}**"
        for name, value in rules.items()
    )
    markdown.extend(["", "## Column Profile", "", markdown_table(quality_report)])
    markdown.extend(["", "## Category Summary", "", markdown_table(category_summary, include_index=True)])
    (report_dir / "data_profile.md").write_text("\n".join(markdown), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile the raw e-commerce CSV dataset.")
    parser.add_argument(
        "input_path",
        type=Path,
        nargs="?",
        default=DEFAULT_DATASET_PATH,
        help="Path to the raw CSV; defaults to DATASET_PATH or the supplied dataset.",
    )
    parser.add_argument("--report-dir", type=Path, default=Path("data/reports"))
    args = parser.parse_args()
    profile_dataset(args.input_path, args.report_dir)
    print(f"Profile written to {args.report_dir.resolve()}")


if __name__ == "__main__":
    main()