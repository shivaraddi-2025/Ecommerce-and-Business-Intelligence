from __future__ import annotations

import datetime as dt
import hashlib
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pandas as pd
import pymysql
from pymysql.cursors import DictCursor

from .database import _load_env  # noqa: F401

_load_env()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "nexus_commerce_bi")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")


@contextmanager
def db_conn(**kw) -> Iterator[pymysql.Connection]:
    kw.setdefault("host", DB_HOST)
    kw.setdefault("port", DB_PORT)
    kw.setdefault("user", DB_USER)
    kw.setdefault("password", DB_PASSWORD)
    kw.setdefault("database", DB_NAME)
    kw.setdefault("charset", DB_CHARSET)
    kw.setdefault("cursorclass", DictCursor)
    conn = pymysql.connect(**kw)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_tables_exist() -> None:
    TABLES_SQL = [
        """CREATE TABLE IF NOT EXISTS locations (
            id INT PRIMARY KEY AUTO_INCREMENT,
            region VARCHAR(100) NOT NULL,
            state_name VARCHAR(150) NOT NULL,
            city VARCHAR(150) NOT NULL,
            postal_code VARCHAR(32) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_loc (region, state_name, city, postal_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
        """CREATE TABLE IF NOT EXISTS customers (
            id INT PRIMARY KEY AUTO_INCREMENT,
            customer_id VARCHAR(64) NOT NULL UNIQUE,
            customer_name VARCHAR(255) NULL,
            segment VARCHAR(100) NULL,
            location_id INT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_cust_loc (location_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
        """CREATE TABLE IF NOT EXISTS categories (
            id INT PRIMARY KEY AUTO_INCREMENT,
            category VARCHAR(150) NOT NULL UNIQUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
        """CREATE TABLE IF NOT EXISTS products (
            id INT PRIMARY KEY AUTO_INCREMENT,
            product_id VARCHAR(64) NOT NULL UNIQUE,
            product_name VARCHAR(500) NOT NULL,
            category_id INT NULL,
            sub_category VARCHAR(200) NULL,
            unit_price DECIMAL(16,4) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_prod_cat (category_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
        """CREATE TABLE IF NOT EXISTS orders (
            id INT PRIMARY KEY AUTO_INCREMENT,
            order_id VARCHAR(64) NOT NULL UNIQUE,
            order_date DATE NOT NULL,
            ship_date DATE NULL,
            ship_mode VARCHAR(100) NULL,
            customer_id INT NULL,
            location_id INT NULL,
            order_priority VARCHAR(64) NULL,
            total_sales DECIMAL(18,4) NOT NULL DEFAULT 0,
            total_quantity INT NOT NULL DEFAULT 0,
            total_profit DECIMAL(18,4) NOT NULL DEFAULT 0,
            total_discount DECIMAL(10,4) NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_orders_date (order_date),
            KEY idx_orders_cust (customer_id),
            KEY idx_orders_loc (location_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
        """CREATE TABLE IF NOT EXISTS order_items (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            order_id INT NOT NULL,
            product_id INT NULL,
            sales DECIMAL(16,4) NOT NULL,
            quantity INT NOT NULL,
            discount DECIMAL(8,4) NOT NULL DEFAULT 0,
            profit DECIMAL(16,4) NULL,
            shipping_cost DECIMAL(14,4) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_item_order (order_id),
            KEY idx_item_product (product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
        """CREATE TABLE IF NOT EXISTS returns (
            id INT PRIMARY KEY AUTO_INCREMENT,
            order_id INT NULL,
            product_id INT NULL,
            quantity_returned INT NOT NULL DEFAULT 0,
            amount_returned DECIMAL(16,4) NOT NULL DEFAULT 0,
            reason VARCHAR(255) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_ret_order (order_id),
            KEY idx_ret_prod (product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
        """CREATE TABLE IF NOT EXISTS daily_sales_agg (
            day DATE PRIMARY KEY,
            revenue DECIMAL(18,4) NOT NULL,
            profit DECIMAL(18,4) NOT NULL,
            orders INT NOT NULL,
            items_sold INT NOT NULL,
            avg_order_value DECIMAL(18,4) NOT NULL,
            customers_count INT NOT NULL,
            units_per_order DECIMAL(10,4) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    ]
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            for sql in TABLES_SQL:
                cur.execute(sql)
    except Exception:
        pass


def _normalize_csv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    actual = {c.lower(): c for c in df.columns}

    def _h(s: str) -> str:
        return hashlib.md5(str(s).encode("utf-8")).hexdigest()[:10]

    if "order_id" not in df.columns and "Order ID" in df.columns:
        df["order_id"] = df["Order ID"]
    if "order_date" not in df.columns and "Order Date" in df.columns:
        df["order_date"] = df["Order Date"]
    if "customer_id" not in df.columns and "Customer ID" in df.columns:
        df["customer_id"] = df["Customer ID"]
    if "customer_segment" not in df.columns:
        if "Segment" in df.columns:
            df["customer_segment"] = df["Segment"]
        elif "segment" in df.columns:
            df["customer_segment"] = df["segment"]
    if "product_category" not in df.columns:
        if "Category" in df.columns:
            df["product_category"] = df["Category"]
        elif "category" in df.columns:
            df["product_category"] = df["category"]
    if "product_name" not in df.columns and "Product Name" in df.columns:
        df["product_name"] = df["Product Name"]
    if "quantity" not in df.columns and "Quantity" in df.columns:
        df["quantity"] = df["Quantity"]
    if "unit_price" not in df.columns and "unit price" in actual:
        df["unit_price"] = df[actual["unit price"]]
    if "net_amount" not in df.columns:
        if "Sales" in df.columns:
            df["net_amount"] = df["Sales"]
        elif "sales" in df.columns:
            df["net_amount"] = df["sales"]
    if "discount_pct" not in df.columns and "Discount" in df.columns:
        d = pd.to_numeric(df["Discount"], errors="coerce").fillna(0)
        df["discount_pct"] = np.where(d > 1.0, d, d * 100.0)
    if "discount_amount" not in df.columns:
        df["discount_amount"] = 0
    if "payment_method" not in df.columns:
        df["payment_method"] = "Unknown"
    if "region" not in df.columns and "Region" in df.columns:
        df["region"] = df["Region"]
    if "city" not in df.columns:
        if "City" in df.columns:
            df["city"] = df["City"]
        elif "State" in df.columns:
            df["city"] = df["State"]
    if "order_status" not in df.columns:
        if "Return Status" in df.columns:
            df["order_status"] = df["Return Status"]
        else:
            df["order_status"] = "Delivered"

    df["order_id"] = df.get("order_id", pd.Series(range(len(df)))).astype(str)
    odt = pd.to_datetime(df.get("order_date", pd.Timestamp.now()), errors="coerce")
    df["order_date"] = odt.dt.date
    df["ship_date"] = (odt + pd.Timedelta(days=3)).dt.date
    df["ship_mode"] = "Standard Class"
    df["order_priority"] = "Medium"
    df["customer_id"] = df.get("customer_id", pd.Series("CUST00001", index=df.index)).astype(str)
    df["customer_name"] = df["customer_id"]
    df["segment"] = df.get("customer_segment", pd.Series("Consumer", index=df.index)).astype(str).fillna("Consumer")
    df["region"] = df.get("region", pd.Series("Region-1", index=df.index)).astype(str).fillna("Region-1")
    df["state_name"] = df["region"]
    df["city"] = df.get("city", pd.Series("Unknown City", index=df.index)).astype(str).fillna("Unknown City")
    df["postal_code"] = None
    df["category"] = df.get("product_category", pd.Series("Uncategorized", index=df.index)).astype(str).fillna("Uncategorized")
    df["sub_category"] = df["category"]
    df["product_name"] = df.get("product_name", pd.Series("Unknown Product", index=df.index)).astype(str).fillna("Unknown Product")
    df["product_id"] = (df["category"].astype(str).str.slice(0, 3).str.upper() + "-" + df["product_name"].map(_h)).astype(str)
    df["quantity"] = pd.to_numeric(df.get("quantity", 1), errors="coerce").fillna(1).clip(lower=0).astype(int)
    df["unit_price"] = pd.to_numeric(df.get("unit_price", 0.0), errors="coerce").fillna(0.0).astype(float)
    df["sales"] = pd.to_numeric(df.get("net_amount", 0.0), errors="coerce").fillna(0.0).astype(float)
    df["discount"] = pd.to_numeric(df.get("discount_pct", 0.0), errors="coerce").fillna(0.0).astype(float)
    df["profit"] = (df["sales"] * 0.30).astype(float)
    df["shipping_cost"] = pd.to_numeric(df.get("discount_amount", 0.0), errors="coerce").fillna(0.0).astype(float)
    df["returned"] = df.get("order_status", pd.Series("", index=df.index)).astype(str).str.lower().isin({"returned", "refund", "canceled", "cancelled"})
    df["payment_method"] = df.get("payment_method", pd.Series("Unknown", index=df.index)).astype(str).fillna("Unknown")
    return df


def sync_csv_to_db(dataset_path: str | Path, replace_existing: bool = True) -> dict[str, int]:
    _ensure_tables_exist()
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)
    df = _normalize_csv(df)

    with db_conn() as conn:
        cur = conn.cursor()

        if replace_existing:
            for tbl in ["data_quality_columns", "data_quality_runs", "product_recommendations",
                        "top_customers", "top_products", "snapshot_kpis", "snapshot_runs",
                        "daily_forecast", "forecast_runs", "daily_sales_agg",
                        "returns", "order_items", "orders", "products", "categories",
                        "customers", "locations"]:
                try:
                    cur.execute(f"TRUNCATE TABLE {tbl}")
                except Exception:
                    try:
                        cur.execute(f"DELETE FROM {tbl}")
                    except Exception:
                        pass

        loc_df = df[["region", "state_name", "city", "postal_code"]].drop_duplicates().reset_index(drop=True)
        loc_df["postal_code"] = loc_df["postal_code"].astype(object).where(loc_df["postal_code"].notna(), None)
        loc_rows = list(loc_df.itertuples(index=False, name=None))
        cur.executemany(
            "INSERT IGNORE INTO locations (region, state_name, city, postal_code) VALUES (%s, %s, %s, %s)",
            loc_rows,
        )
        cur.execute("SELECT id, region, state_name, city, postal_code FROM locations")
        loc_map = {(r["region"], r["state_name"], r["city"], r["postal_code"]): r["id"] for r in cur.fetchall()}

        cust_df = df[["customer_id", "customer_name", "segment", "region", "state_name", "city", "postal_code"]].drop_duplicates(subset=["customer_id"]).reset_index(drop=True)
        cust_rows = []
        for r in cust_df.itertuples(index=False, name=None):
            cid, cname, seg, reg, st, cy, pc = r
            pc = pc if pd.notna(pc) else None
            loc_key = (reg, st, cy, pc)
            loc_id = loc_map.get(loc_key)
            cust_rows.append((cid, cname if pd.notna(cname) else None, seg if pd.notna(seg) else None, loc_id))
        cur.executemany(
            "INSERT IGNORE INTO customers (customer_id, customer_name, segment, location_id) VALUES (%s, %s, %s, %s)",
            cust_rows,
        )
        cur.execute("SELECT id, customer_id FROM customers")
        cust_map = {r["customer_id"]: r["id"] for r in cur.fetchall()}

        cat_df = pd.DataFrame({"category": df["category"].dropna().unique()})
        cat_rows = list(cat_df.itertuples(index=False, name=None))
        cur.executemany("INSERT IGNORE INTO categories (category) VALUES (%s)", cat_rows)
        cur.execute("SELECT id, category FROM categories")
        cat_map = {r["category"]: r["id"] for r in cur.fetchall()}

        prod_df = df[["product_id", "product_name", "category", "sub_category", "sales", "quantity"]].copy()
        prod_df["unit_price"] = (prod_df["sales"] / prod_df["quantity"].clip(lower=1)).fillna(0)
        prod_df = prod_df.drop_duplicates(subset=["product_id"]).reset_index(drop=True)
        prod_rows = []
        for r in prod_df.itertuples(index=False, name=None):
            pid, pname, cat, sub, _s, _q, up = r
            prod_rows.append((pid, pname, cat_map.get(cat), sub if pd.notna(sub) else None, float(up)))
        cur.executemany(
            "INSERT IGNORE INTO products (product_id, product_name, category_id, sub_category, unit_price) VALUES (%s, %s, %s, %s, %s)",
            prod_rows,
        )
        cur.execute("SELECT id, product_id FROM products")
        prod_map = {r["product_id"]: r["id"] for r in cur.fetchall()}

        order_df = df[["order_id", "order_date", "ship_date", "ship_mode", "customer_id", "region", "state_name", "city", "postal_code", "order_priority"]].copy()
        order_df["ship_date"] = order_df["ship_date"].where(order_df["ship_date"].notna(), None)
        order_df = order_df.drop_duplicates(subset=["order_id"]).reset_index(drop=True)
        order_rows = []
        for r in order_df.itertuples(index=False, name=None):
            oid, odt, sdt, sm, cid, reg, st, cy, pc, prio = r
            pc = pc if pd.notna(pc) else None
            loc_id = loc_map.get((reg, st, cy, pc))
            cid_int = cust_map.get(cid)
            odt2 = odt.date() if isinstance(odt, dt.datetime) else odt if isinstance(odt, dt.date) else None
            sdt2 = sdt.date() if isinstance(sdt, dt.datetime) else sdt if isinstance(sdt, dt.date) else None
            order_rows.append((oid, odt2, sdt2, sm if pd.notna(sm) else None, cid_int, loc_id, prio if pd.notna(prio) else None))
        cur.executemany(
            "INSERT IGNORE INTO orders (order_id, order_date, ship_date, ship_mode, customer_id, location_id, order_priority) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            order_rows,
        )
        cur.execute("SELECT id, order_id FROM orders")
        order_map = {r["order_id"]: r["id"] for r in cur.fetchall()}

        item_rows = []
        for r in df.itertuples(index=False):
            oid_db = order_map.get(r.order_id)
            pid_db = prod_map.get(r.product_id)
            if oid_db is None:
                continue
            qty = int(r.quantity) if pd.notna(r.quantity) else 1
            discount = float(r.discount) if pd.notna(r.discount) else 0.0
            profit = float(r.profit) if pd.notna(r.profit) else None
            ship_cost = float(r.shipping_cost) if pd.notna(r.shipping_cost) else None
            item_rows.append((oid_db, pid_db, float(r.sales), qty, discount, profit, ship_cost))

        BATCH = 10000
        for i in range(0, len(item_rows), BATCH):
            batch = item_rows[i:i + BATCH]
            cur.executemany(
                "INSERT INTO order_items (order_id, product_id, sales, quantity, discount, profit, shipping_cost) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                batch,
            )

        cur.execute("""
            UPDATE orders O JOIN (
              SELECT order_id,
                     SUM(sales) total_sales,
                     SUM(quantity) total_quantity,
                     SUM(COALESCE(profit,0)) total_profit,
                     SUM(discount) total_discount
              FROM order_items GROUP BY order_id
            ) I ON I.order_id = O.id
            SET O.total_sales = I.total_sales,
                O.total_quantity = I.total_quantity,
                O.total_profit = I.total_profit,
                O.total_discount = I.total_discount;
        """)

        returns_df = df[df["returned"].astype(str).str.lower().isin({"1", "true", "yes", "y"})].copy()
        if len(returns_df):
            ret_rows = []
            for r in returns_df.itertuples(index=False):
                oid_db = order_map.get(r.order_id)
                pid_db = prod_map.get(r.product_id)
                qty = int(r.quantity) if pd.notna(r.quantity) else 1
                ret_rows.append((oid_db, pid_db, qty, float(r.sales), "CSV returned flag"))
            if ret_rows:
                cur.executemany(
                    "INSERT INTO returns (order_id, product_id, quantity_returned, amount_returned, reason) VALUES (%s, %s, %s, %s, %s)",
                    ret_rows,
                )

        counts = {
            "locations": len(loc_map),
            "customers": len(cust_map),
            "categories": len(cat_map),
            "products": len(prod_map),
            "orders": len(order_map),
            "order_items": len(item_rows),
        }

        try:
            daily = df.groupby(df["order_date"]).agg(
                revenue=("sales", "sum"),
                profit=("profit", "sum"),
                orders=("order_id", "nunique"),
                items_sold=("quantity", "sum"),
                customers_count=("customer_id", "nunique"),
            ).reset_index()
            daily = daily.rename(columns={"order_date": "day"})
            daily["avg_order_value"] = np.where(daily["orders"] > 0, daily["revenue"] / daily["orders"], 0)
            daily["units_per_order"] = np.where(daily["orders"] > 0, daily["items_sold"] / daily["orders"], 0)
            daily_rows = [
                (
                    r["day"],
                    float(r["revenue"]),
                    float(r["profit"]),
                    int(r["orders"]),
                    int(r["items_sold"]),
                    float(r["avg_order_value"]),
                    int(r["customers_count"]),
                    float(r["units_per_order"]),
                )
                for _, r in daily.iterrows()
            ]
            if daily_rows:
                cur.executemany(
                    """REPLACE INTO daily_sales_agg (day, revenue, profit, orders, items_sold, avg_order_value, customers_count, units_per_order)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    daily_rows,
                )
            counts["daily_sales_agg"] = len(daily_rows)
        except Exception:
            counts["daily_sales_agg"] = 0

    return counts


def _row_to_normalized(data: dict[str, Any]) -> pd.DataFrame:
    df = pd.DataFrame([data])
    return _normalize_csv(df)


def upsert_sale_to_db(data: dict[str, Any]) -> dict[str, Any] | None:
    try:
        _ensure_tables_exist()
        ndf = _row_to_normalized(data)
        if ndf.empty:
            return None
        row = ndf.iloc[0]

        with db_conn() as conn:
            cur = conn.cursor()

            loc_key = (row["region"], row["state_name"], row["city"], None)
            cur.execute(
                "INSERT IGNORE INTO locations (region, state_name, city, postal_code) VALUES (%s, %s, %s, %s)",
                loc_key,
            )
            cur.execute(
                "SELECT id FROM locations WHERE region=%s AND state_name=%s AND city=%s AND postal_code IS NULL LIMIT 1",
                (row["region"], row["state_name"], row["city"]),
            )
            res = cur.fetchone()
            loc_id = res["id"] if res else None

            cur.execute(
                "INSERT IGNORE INTO customers (customer_id, customer_name, segment, location_id) VALUES (%s, %s, %s, %s)",
                (row["customer_id"], row["customer_name"], row["segment"], loc_id),
            )
            cur.execute("SELECT id FROM customers WHERE customer_id=%s LIMIT 1", (row["customer_id"],))
            res = cur.fetchone()
            cid_int = res["id"] if res else None

            cur.execute("INSERT IGNORE INTO categories (category) VALUES (%s)", (row["category"],))
            cur.execute("SELECT id FROM categories WHERE category=%s LIMIT 1", (row["category"],))
            res = cur.fetchone()
            cat_id = res["id"] if res else None

            unit_price = float(row["unit_price"]) if row.get("unit_price") else 0.0
            cur.execute(
                "INSERT IGNORE INTO products (product_id, product_name, category_id, sub_category, unit_price) VALUES (%s, %s, %s, %s, %s)",
                (row["product_id"], row["product_name"], cat_id, row["sub_category"], unit_price),
            )
            cur.execute("SELECT id FROM products WHERE product_id=%s LIMIT 1", (row["product_id"],))
            res = cur.fetchone()
            pid_db = res["id"] if res else None

            cur.execute(
                """INSERT INTO orders (order_id, order_date, ship_date, ship_mode, customer_id, location_id, order_priority)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                     order_date=VALUES(order_date), ship_date=VALUES(ship_date), ship_mode=VALUES(ship_mode),
                     customer_id=VALUES(customer_id), location_id=VALUES(location_id), order_priority=VALUES(order_priority)""",
                (row["order_id"], row["order_date"], row["ship_date"], row["ship_mode"], cid_int, loc_id, row["order_priority"]),
            )
            cur.execute("SELECT id FROM orders WHERE order_id=%s LIMIT 1", (row["order_id"],))
            res = cur.fetchone()
            oid_db = res["id"] if res else None

            if oid_db:
                cur.execute("DELETE FROM order_items WHERE order_id=%s", (oid_db,))
                cur.execute(
                    """INSERT INTO order_items (order_id, product_id, sales, quantity, discount, profit, shipping_cost)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (oid_db, pid_db, float(row["sales"]), int(row["quantity"]),
                     float(row["discount"]), float(row["profit"]), float(row["shipping_cost"])),
                )
                cur.execute(
                    """UPDATE orders SET
                         total_sales = (SELECT COALESCE(SUM(sales),0) FROM order_items WHERE order_id=%s),
                         total_quantity = (SELECT COALESCE(SUM(quantity),0) FROM order_items WHERE order_id=%s),
                         total_profit = (SELECT COALESCE(SUM(profit),0) FROM order_items WHERE order_id=%s),
                         total_discount = (SELECT COALESCE(SUM(discount),0) FROM order_items WHERE order_id=%s)
                       WHERE id=%s""",
                    (oid_db, oid_db, oid_db, oid_db, oid_db),
                )
                if bool(row.get("returned")):
                    cur.execute("DELETE FROM returns WHERE order_id=%s", (oid_db,))
                    cur.execute(
                        "INSERT INTO returns (order_id, product_id, quantity_returned, amount_returned, reason) VALUES (%s, %s, %s, %s, %s)",
                        (oid_db, pid_db, int(row["quantity"]), float(row["sales"]), "Sale record flag"),
                    )
                else:
                    cur.execute("DELETE FROM returns WHERE order_id=%s", (oid_db,))

        return {"order_id": row["order_id"], "status": "synced"}
    except Exception:
        return None


def delete_sale_from_db(order_id: str) -> bool:
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM orders WHERE order_id=%s LIMIT 1", (order_id,))
            res = cur.fetchone()
            if not res:
                return True
            oid_db = res["id"]
            cur.execute("DELETE FROM returns WHERE order_id=%s", (oid_db,))
            cur.execute("DELETE FROM order_items WHERE order_id=%s", (oid_db,))
            cur.execute("DELETE FROM orders WHERE id=%s", (oid_db,))
        return True
    except Exception:
        return False
