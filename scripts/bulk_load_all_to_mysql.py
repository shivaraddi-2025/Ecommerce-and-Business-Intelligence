from __future__ import annotations

import base64
import datetime as dt
import hashlib
import os
import secrets
from pathlib import Path

import pandas as pd
import pymysql
from pymysql.cursors import DictCursor

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "raw" / "ecommerce_sales_raw.csv.csv"
ENV_PATH = ROOT / ".env"

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "MySQL@2026"
DB_NAME = "nexus_commerce_bi"
DB_CHARSET = "utf8mb4"

VALID_ROLES = {"Admin", "Business Manager", "Analyst", "Viewer"}


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return base64.b64encode(salt + digest).decode()


def update_env_db_name() -> None:
    lines = []
    replaced = False
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.rstrip("\n")
            if line.lower().startswith("db_name="):
                lines.append(f"DB_NAME={DB_NAME}")
                replaced = True
            else:
                lines.append(line)
    if not replaced:
        lines.append(f"DB_NAME={DB_NAME}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ["DB_NAME"] = DB_NAME


CREATE_SCHEMA_SQL = f"""
CREATE DATABASE IF NOT EXISTS `{DB_NAME}`
CHARACTER SET {DB_CHARSET}
COLLATE {DB_CHARSET}_unicode_ci;
USE `{DB_NAME}`;
"""

CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(512) NOT NULL,
        role VARCHAR(64) NOT NULL DEFAULT 'Viewer',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        KEY idx_users_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS locations (
        id INT PRIMARY KEY AUTO_INCREMENT,
        region VARCHAR(100) NOT NULL,
        state_name VARCHAR(150) NOT NULL,
        city VARCHAR(150) NOT NULL,
        postal_code VARCHAR(32) NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_loc (region, state_name, city, postal_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS customers (
        id INT PRIMARY KEY AUTO_INCREMENT,
        customer_id VARCHAR(64) NOT NULL UNIQUE,
        customer_name VARCHAR(255) NULL,
        segment VARCHAR(100) NULL,
        location_id INT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        KEY idx_cust_loc (location_id),
        CONSTRAINT fk_cust_loc FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        id INT PRIMARY KEY AUTO_INCREMENT,
        category VARCHAR(150) NOT NULL UNIQUE,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        id INT PRIMARY KEY AUTO_INCREMENT,
        product_id VARCHAR(64) NOT NULL UNIQUE,
        product_name VARCHAR(500) NOT NULL,
        category_id INT NULL,
        sub_category VARCHAR(200) NULL,
        unit_price DECIMAL(16,4) NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        KEY idx_prod_cat (category_id),
        CONSTRAINT fk_prod_cat FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
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
        KEY idx_orders_loc (location_id),
        CONSTRAINT fk_orders_cust FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
        CONSTRAINT fk_orders_loc FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS order_items (
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
        KEY idx_item_product (product_id),
        CONSTRAINT fk_item_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        CONSTRAINT fk_item_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS returns (
        id INT PRIMARY KEY AUTO_INCREMENT,
        order_id INT NULL,
        product_id INT NULL,
        quantity_returned INT NOT NULL DEFAULT 0,
        amount_returned DECIMAL(16,4) NOT NULL DEFAULT 0,
        reason VARCHAR(255) NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        KEY idx_ret_order (order_id),
        KEY idx_ret_prod (product_id),
        CONSTRAINT fk_ret_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
        CONSTRAINT fk_ret_prod FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_sales_agg (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_forecast (
        forecast_run_id INT NOT NULL,
        forecast_day DATE NOT NULL,
        forecast_revenue DECIMAL(18,4) NOT NULL,
        forecast_profit DECIMAL(18,4) NOT NULL,
        forecast_orders INT NOT NULL,
        forecast_quantity INT NOT NULL,
        lower_bound_revenue DECIMAL(18,4) NULL,
        upper_bound_revenue DECIMAL(18,4) NULL,
        confidence DECIMAL(5,4) NULL,
        baseline_mae DECIMAL(18,4) NULL,
        model_mae DECIMAL(18,4) NULL,
        is_model_better TINYINT(1) NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (forecast_run_id, forecast_day),
        KEY idx_fc_day (forecast_day)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS forecast_runs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        forecast_days INT NOT NULL,
        model_name VARCHAR(100) NOT NULL,
        r2_score DECIMAL(9,6) NULL,
        test_mae DECIMAL(18,4) NULL,
        baseline_mae DECIMAL(18,4) NULL,
        is_model_better TINYINT(1) NOT NULL DEFAULT 0,
        last_historical_day DATE NULL,
        notes VARCHAR(500) NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS snapshot_runs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        filters_json JSON NULL,
        records_scanned INT NOT NULL,
        notes VARCHAR(500) NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS snapshot_kpis (
        snapshot_id INT NOT NULL,
        kpi_name VARCHAR(128) NOT NULL,
        kpi_value DECIMAL(22,6) NOT NULL,
        unit VARCHAR(32) NULL,
        delta_prev_period DECIMAL(18,6) NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (snapshot_id, kpi_name),
        CONSTRAINT fk_kpi_snap FOREIGN KEY (snapshot_id) REFERENCES snapshot_runs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS top_products (
        snapshot_id INT NOT NULL,
        rank_no INT NOT NULL,
        product_id VARCHAR(64) NOT NULL,
        product_name VARCHAR(500) NOT NULL,
        category VARCHAR(200) NULL,
        sales DECIMAL(18,4) NOT NULL,
        quantity INT NOT NULL,
        profit DECIMAL(18,4) NULL,
        score DECIMAL(18,6) NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (snapshot_id, rank_no),
        CONSTRAINT fk_tp_snap FOREIGN KEY (snapshot_id) REFERENCES snapshot_runs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS top_customers (
        snapshot_id INT NOT NULL,
        rank_no INT NOT NULL,
        customer_id VARCHAR(64) NOT NULL,
        customer_name VARCHAR(255) NULL,
        segment VARCHAR(100) NULL,
        orders INT NOT NULL,
        sales DECIMAL(18,4) NOT NULL,
        profit DECIMAL(18,4) NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (snapshot_id, rank_no),
        CONSTRAINT fk_tc_snap FOREIGN KEY (snapshot_id) REFERENCES snapshot_runs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS product_recommendations (
        snapshot_id INT NOT NULL,
        rank_no INT NOT NULL,
        product_id VARCHAR(64) NOT NULL,
        product_name VARCHAR(500) NOT NULL,
        category VARCHAR(200) NULL,
        score DECIMAL(18,6) NOT NULL,
        sales_rank_pct DECIMAL(9,6) NULL,
        profit_rank_pct DECIMAL(9,6) NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (snapshot_id, rank_no),
        CONSTRAINT fk_rec_snap FOREIGN KEY (snapshot_id) REFERENCES snapshot_runs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS data_quality_runs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        overall_score DECIMAL(8,5) NOT NULL,
        row_count BIGINT NOT NULL,
        column_count INT NOT NULL,
        duplicate_rows BIGINT NOT NULL,
        null_cells BIGINT NOT NULL,
        data_path VARCHAR(500) NULL,
        notes VARCHAR(500) NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS data_quality_columns (
        run_id INT NOT NULL,
        column_name VARCHAR(128) NOT NULL,
        dtype VARCHAR(64) NULL,
        non_null_count BIGINT NOT NULL,
        null_count BIGINT NOT NULL,
        unique_count BIGINT NULL,
        min_value VARCHAR(255) NULL,
        max_value VARCHAR(255) NULL,
        mean_value DECIMAL(22,6) NULL,
        stddev_value DECIMAL(22,6) NULL,
        rules_passed INT NULL,
        rules_total INT NULL,
        issues_json JSON NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, column_name),
        CONSTRAINT fk_dqc_run FOREIGN KEY (run_id) REFERENCES data_quality_runs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]


def root_connect(**kw):
    return pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, charset="utf8mb4", **kw)


def db_connect(**kw):
    return pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, charset="utf8mb4", **kw)


def ensure_schema_and_tables() -> None:
    with root_connect() as c:
        with c.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`;")
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                f"CHARACTER SET {DB_CHARSET} COLLATE {DB_CHARSET}_unicode_ci;"
            )
        c.commit()
    with db_connect() as c:
        with c.cursor() as cur:
            for sql in CREATE_TABLES_SQL:
                cur.execute(sql)
        c.commit()


def seed_users() -> None:
    admin_email = (os.getenv("ADMIN_EMAIL") or "demo@example.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD") or "demo-password"
    demo_email = "demo@example.com"
    demo_password = "demo-password"
    with db_connect() as c:
        with c.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            if cur.fetchone()[0] == 0:
                rows = [
                    (admin_email, _hash_password(admin_password), "Admin"),
                ]
                if admin_email != demo_email:
                    rows.append((demo_email, _hash_password(demo_password), "Admin"))
                cur.executemany(
                    "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
                    rows,
                )
        c.commit()


def load_raw_csv() -> pd.DataFrame:
    import hashlib

    df = pd.read_csv(DATASET_PATH)
    df.columns = [str(c).strip() for c in df.columns]

    actual = {c.lower(): c for c in df.columns}
    col_map = {
        "order_id": actual.get("order_id", None),
        "order_date": actual.get("order_date", None),
        "order_datetime": actual.get("order_datetime", None),
        "customer_id": actual.get("customer_id", None),
        "customer_segment": actual.get("customer_segment", None),
        "product_category": actual.get("product_category", None),
        "product_name": actual.get("product_name", None),
        "quantity": actual.get("quantity", None),
        "unit_price": actual.get("unit_price", None),
        "gross_amount": actual.get("gross_amount", None),
        "discount_pct": actual.get("discount_pct", None),
        "discount_amount": actual.get("discount_amount", None),
        "net_amount": actual.get("net_amount", None),
        "payment_method": actual.get("payment_method", None),
        "region": actual.get("region", None),
        "city": actual.get("city", None),
        "order_status": actual.get("order_status", None),
        "day_of_week": actual.get("day_of_week", None),
        "month": actual.get("month", None),
        "year": actual.get("year", None),
    }

    def _h(s: str) -> str:
        return hashlib.md5(str(s).encode("utf-8")).hexdigest()[:10]

    df["order_id"] = df[col_map["order_id"]].astype(str)
    odt = pd.to_datetime(df[col_map["order_date"]] if col_map["order_date"] is not None else df[col_map["order_datetime"]], errors="coerce")
    df["order_date"] = odt.dt.date
    df["ship_date"] = (odt + pd.Timedelta(days=3)).dt.date
    df["ship_mode"] = "Standard Class"
    df["order_priority"] = "Medium"
    df["customer_id"] = df[col_map["customer_id"]].astype(str)
    df["customer_name"] = df["customer_id"]
    df["segment"] = df[col_map["customer_segment"]].astype(str).fillna("Consumer")
    df["region"] = df[col_map["region"]].astype(str).fillna("Region-1")
    df["state"] = df["region"]
    df["city"] = df[col_map["city"]].astype(str).fillna("Unknown City")
    df["postal_code"] = None
    df["category"] = df[col_map["product_category"]].astype(str).fillna("Uncategorized")
    df["sub_category"] = df["category"]
    df["product_name"] = df[col_map["product_name"]].astype(str).fillna("Unknown Product")
    df["product_id"] = (df["category"].astype(str).str.slice(0, 3).str.upper() + "-" + df["product_name"].map(_h)).astype(str)
    df["quantity"] = pd.to_numeric(df[col_map["quantity"]], errors="coerce").fillna(1).clip(lower=0).astype(int)
    df["unit_price"] = pd.to_numeric(df[col_map["unit_price"]], errors="coerce").fillna(0.0).astype(float)
    df["sales"] = pd.to_numeric(df[col_map["net_amount"]], errors="coerce").fillna(0.0).astype(float)
    df["discount"] = pd.to_numeric(df[col_map["discount_pct"]], errors="coerce").fillna(0.0).astype(float)
    df["profit"] = (df["sales"] * 0.30).astype(float)
    df["shipping_cost"] = pd.to_numeric(df[col_map["discount_amount"]], errors="coerce").fillna(0.0).astype(float)
    df["returned"] = (df[col_map["order_status"]].astype(str).str.lower().isin({"returned","refund"}))
    df["payment_method"] = df[col_map["payment_method"]].astype(str).fillna("Unknown")

    df["state_name"] = df["state"]
    return df


def bulk_load_star_schema(df: pd.DataFrame) -> None:
    with db_connect(cursorclass=DictCursor) as conn:
        cur = conn.cursor()

        loc_df = df[["region","state_name","city","postal_code"]].drop_duplicates().reset_index(drop=True)
        loc_df["postal_code"] = loc_df["postal_code"].astype(object).where(loc_df["postal_code"].notna(), None)
        loc_rows = list(loc_df.itertuples(index=False, name=None))
        cur.executemany(
            "INSERT IGNORE INTO locations (region, state_name, city, postal_code) VALUES (%s, %s, %s, %s)",
            loc_rows,
        )
        cur.execute("SELECT id, region, state_name, city, postal_code FROM locations")
        loc_map = {(r["region"], r["state_name"], r["city"], r["postal_code"]): r["id"] for r in cur.fetchall()}
        print(f"locations: {len(loc_map)}")

        cust_df = df[["customer_id","customer_name","segment","region","state_name","city","postal_code"]].drop_duplicates(subset=["customer_id"]).reset_index(drop=True)
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
        print(f"customers: {len(cust_map)}")

        cat_df = pd.DataFrame({"category": df["category"].dropna().unique()})
        cat_rows = list(cat_df.itertuples(index=False, name=None))
        cur.executemany("INSERT IGNORE INTO categories (category) VALUES (%s)", cat_rows)
        cur.execute("SELECT id, category FROM categories")
        cat_map = {r["category"]: r["id"] for r in cur.fetchall()}
        print(f"categories: {len(cat_map)}")

        prod_df = df[["product_id","product_name","category","sub_category","sales","quantity"]].copy()
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
        print(f"products: {len(prod_map)}")

        order_df = df[["order_id","order_date","ship_date","ship_mode","customer_id","region","state_name","city","postal_code","order_priority"]].copy()
        order_df["ship_date"] = order_df["ship_date"].where(order_df["ship_date"].notna(), None)
        order_df = order_df.drop_duplicates(subset=["order_id"]).reset_index(drop=True)
        order_rows = []
        for r in order_df.itertuples(index=False, name=None):
            oid, odt, sdt, sm, cid, reg, st, cy, pc, prio = r
            pc = pc if pd.notna(pc) else None
            loc_id = loc_map.get((reg, st, cy, pc))
            cid_int = cust_map.get(cid)
            if isinstance(odt, dt.datetime):
                odt2 = odt.date()
            elif isinstance(odt, dt.date):
                odt2 = odt
            else:
                odt2 = None
            if isinstance(sdt, dt.datetime):
                sdt2 = sdt.date()
            elif isinstance(sdt, dt.date):
                sdt2 = sdt
            else:
                sdt2 = None
            order_rows.append((oid, odt2, sdt2, sm if pd.notna(sm) else None, cid_int, loc_id, prio if pd.notna(prio) else None))
        cur.executemany(
            "INSERT IGNORE INTO orders (order_id, order_date, ship_date, ship_mode, customer_id, location_id, order_priority) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            order_rows,
        )
        cur.execute("SELECT id, order_id FROM orders")
        order_map = {r["order_id"]: r["id"] for r in cur.fetchall()}
        print(f"orders: {len(order_map)}")

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
            batch = item_rows[i:i+BATCH]
            cur.executemany(
                "INSERT INTO order_items (order_id, product_id, sales, quantity, discount, profit, shipping_cost) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                batch,
            )
        print(f"order_items: {len(item_rows)}")

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

        returns_df = df[df["returned"].astype(str).str.lower().isin({"1","true","yes","y"})].copy() if "returned" in df.columns else df.head(0)
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
                print(f"returns: {len(ret_rows)}")

        conn.commit()


def compute_and_load_daily_sales_and_forecast(df: pd.DataFrame) -> None:
    from backend.app.analytics import AnalyticsEngine

    engine = AnalyticsEngine(DATASET_PATH)
    daily = engine.daily_sales_report()
    day_df = pd.DataFrame(daily["daily"])
    if not day_df.empty:
        day_df["date"] = pd.to_datetime(day_df["date"]).dt.date
        rows = [
            (
                r["date"],
                float(r["revenue"]),
                float(r.get("profit") or 0),
                int(r.get("orders") or 0),
                int(r.get("items_sold") or 0),
                float(r.get("avg_order_value") or 0),
                int(r.get("customers") or 0),
                float(r.get("items_sold") or 0) / max(int(r.get("orders") or 0), 1),
            )
            for _, r in day_df.iterrows()
        ]
        with db_connect() as c:
            with c.cursor() as cur:
                cur.executemany(
                    """
                    REPLACE INTO daily_sales_agg (day, revenue, profit, orders, items_sold, avg_order_value, customers_count, units_per_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    rows,
                )
            c.commit()
        print(f"daily_sales_agg: {len(rows)}")

    forecast = engine.daily_sales_forecast(days=30)
    last_hist_day = day_df["date"].max() if not day_df.empty else (pd.Timestamp.utcnow() - pd.Timedelta(days=1)).date()
    with db_connect(cursorclass=DictCursor) as c:
        with c.cursor() as cur:
            model_name = "RandomForestRegressor(n_estimators=300)"
            baseline_mae = forecast.get("baseline_mae")
            model_mae = forecast.get("model_mae")
            r2 = forecast.get("r2_score")
            is_better = 1 if forecast.get("model_better") else 0
            cur.execute(
                """
                INSERT INTO forecast_runs (created_at, forecast_days, model_name, r2_score, test_mae, baseline_mae, is_model_better, last_historical_day, notes)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    len(forecast.get("forecast") or []),
                    model_name,
                    float(r2) if r2 is not None else None,
                    float(model_mae) if model_mae is not None else None,
                    float(baseline_mae) if baseline_mae is not None else None,
                    is_better,
                    last_hist_day,
                    "Initial bulk load",
                ),
            )
            run_id = c.insert_id()
            fc_rows = []
            for idx, item in enumerate(forecast.get("forecast") or []):
                d = pd.to_datetime(item["date"]).date()
                fc_rows.append((
                    run_id,
                    d,
                    float(item.get("revenue") or 0),
                    float(item.get("profit") or 0),
                    int(item.get("orders") or 0),
                    int(item.get("quantity") or 0),
                    float(item.get("lower_revenue")) if item.get("lower_revenue") is not None else None,
                    float(item.get("upper_revenue")) if item.get("upper_revenue") is not None else None,
                    float(forecast.get("confidence") or 0),
                    float(baseline_mae) if baseline_mae is not None else None,
                    float(model_mae) if model_mae is not None else None,
                    is_better,
                ))
            if fc_rows:
                cur.executemany(
                    """
                    INSERT INTO daily_forecast (forecast_run_id, forecast_day, forecast_revenue, forecast_profit,
                        forecast_orders, forecast_quantity, lower_bound_revenue, upper_bound_revenue, confidence,
                        baseline_mae, model_mae, is_model_better)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    fc_rows,
                )
                print(f"forecast_runs id={run_id}  daily_forecast rows: {len(fc_rows)}")
        c.commit()


def compute_and_load_snapshots() -> None:
    from backend.app.analytics import AnalyticsEngine
    import json as _json

    engine = AnalyticsEngine(DATASET_PATH)
    dashboard = engine.dashboard_kpis({})
    kpis = dashboard["kpis"]
    filters = {}
    notes = "Initial bulk load — default filters"

    with db_connect(cursorclass=DictCursor) as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO snapshot_runs (created_at, filters_json, records_scanned, notes) VALUES (NOW(), %s, %s, %s)",
                (_json.dumps(filters), int(kpis.get("total_orders") or 0), notes),
            )
            snap_id = c.insert_id()
            kpi_rows = []
            def _add(name: str, value, unit: str | None = None, delta=None) -> None:
                if value is None:
                    return
                try:
                    fval = float(value)
                except (TypeError, ValueError):
                    return
                kpi_rows.append((snap_id, name, fval, unit, float(delta) if delta is not None else None))
            _add("revenue", kpis.get("revenue"), "INR")
            _add("profit", kpis.get("profit"), "INR")
            _add("profit_margin", kpis.get("profit_margin"), "%")
            _add("total_orders", kpis.get("total_orders"), "orders")
            _add("unique_customers", kpis.get("unique_customers"), "customers")
            _add("avg_order_value", kpis.get("avg_order_value"), "INR")
            _add("total_quantity", kpis.get("total_quantity"), "units")
            _add("return_rate", kpis.get("return_rate"), "%")
            _add("revenue_growth_pct", kpis.get("revenue_growth_pct"), "%")
            _add("customers_growth_pct", kpis.get("customers_growth_pct"), "%")
            _add("orders_growth_pct", kpis.get("orders_growth_pct"), "%")
            if kpi_rows:
                cur.executemany(
                    "INSERT INTO snapshot_kpis (snapshot_id, kpi_name, kpi_value, unit, delta_prev_period) VALUES (%s, %s, %s, %s, %s)",
                    kpi_rows,
                )
            top_prod = engine.top_products(top_n=50)
            for i, item in enumerate(top_prod, start=1):
                cur.execute(
                    "INSERT INTO top_products (snapshot_id, rank_no, product_id, product_name, category, sales, quantity, profit, score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        snap_id, i,
                        str(item.get("product_id") or item.get("product_name"))[:64],
                        str(item.get("product_name"))[:500],
                        str(item.get("category") or "")[:200] or None,
                        float(item.get("sales") or 0),
                        int(item.get("quantity") or 0),
                        float(item.get("profit")) if item.get("profit") is not None else None,
                        float(item.get("score")) if item.get("score") is not None else None,
                    ),
                )
            top_cust = engine.top_customers(top_n=50)
            for i, item in enumerate(top_cust, start=1):
                cur.execute(
                    "INSERT INTO top_customers (snapshot_id, rank_no, customer_id, customer_name, segment, orders, sales, profit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        snap_id, i,
                        str(item.get("customer_id") or item.get("customer_name"))[:64],
                        str(item.get("customer_name") or "")[:255] or None,
                        str(item.get("segment") or "")[:100] or None,
                        int(item.get("orders") or 0),
                        float(item.get("sales") or 0),
                        float(item.get("profit")) if item.get("profit") is not None else None,
                    ),
                )
            recs = engine.product_recommendations(top_n=50)
            for i, item in enumerate(recs, start=1):
                cur.execute(
                    "INSERT INTO product_recommendations (snapshot_id, rank_no, product_id, product_name, category, score, sales_rank_pct, profit_rank_pct) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        snap_id, i,
                        str(item.get("product_id") or item.get("product_name"))[:64],
                        str(item.get("product_name"))[:500],
                        str(item.get("category") or "")[:200] or None,
                        float(item.get("score") or 0),
                        float(item.get("sales_rank_pct")) if item.get("sales_rank_pct") is not None else None,
                        float(item.get("profit_rank_pct")) if item.get("profit_rank_pct") is not None else None,
                    ),
                )
        c.commit()
    print("snapshots written, id=", snap_id, "kpis=", len(kpi_rows), "top_products=", len(top_prod), "top_customers=", len(top_cust), "recommendations=", len(recs))


def compute_and_load_quality() -> None:
    import json as _json
    from backend.app.analytics import AnalyticsEngine

    engine = AnalyticsEngine(DATASET_PATH)
    quality = engine.data_quality_report()

    with db_connect(cursorclass=DictCursor) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO data_quality_runs (created_at, overall_score, row_count, column_count, duplicate_rows, null_cells, data_path, notes)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    float(quality.get("overall_score") or 0),
                    int(quality.get("row_count") or 0),
                    int(quality.get("column_count") or 0),
                    int(quality.get("duplicate_rows") or 0),
                    int(quality.get("null_cells") or 0),
                    str(DATASET_PATH),
                    "Initial bulk load",
                ),
            )
            run_id = c.insert_id()
            col_rows = []
            for item in quality.get("columns") or []:
                issues = item.get("issues") or []
                col_rows.append((
                    run_id,
                    str(item["column_name"])[:128],
                    str(item.get("dtype") or "")[:64] or None,
                    int(item.get("non_null_count") or 0),
                    int(item.get("null_count") or 0),
                    int(item["unique_count"]) if item.get("unique_count") is not None else None,
                    str(item.get("min_value") or "")[:255] or None,
                    str(item.get("max_value") or "")[:255] or None,
                    float(item["mean_value"]) if item.get("mean_value") is not None else None,
                    float(item["stddev_value"]) if item.get("stddev_value") is not None else None,
                    int(item.get("rules_passed")) if item.get("rules_passed") is not None else None,
                    int(item.get("rules_total")) if item.get("rules_total") is not None else None,
                    _json.dumps(issues, ensure_ascii=False),
                ))
            cur.executemany(
                """
                INSERT INTO data_quality_columns (run_id, column_name, dtype, non_null_count, null_count, unique_count,
                    min_value, max_value, mean_value, stddev_value, rules_passed, rules_total, issues_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                col_rows,
            )
        c.commit()
    print(f"data_quality_runs id={run_id}  data_quality_columns rows={len(col_rows)}")


def count_all_tables() -> None:
    tables = [
        "users", "locations", "customers", "categories", "products",
        "orders", "order_items", "returns", "daily_sales_agg",
        "forecast_runs", "daily_forecast", "snapshot_runs", "snapshot_kpis",
        "top_products", "top_customers", "product_recommendations",
        "data_quality_runs", "data_quality_columns",
    ]
    with db_connect() as c:
        with c.cursor() as cur:
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                n = cur.fetchone()[0]
                print(f"    {t}: {n} rows")


def main() -> None:
    print("=" * 78)
    print(f"Nexus Commerce Intelligence — fresh full bulk load into MySQL `{DB_NAME}`")
    print("=" * 78)
    print("1. Creating schema + tables ...")
    update_env_db_name()
    ensure_schema_and_tables()
    print("2. Seeding users ...")
    seed_users()
    print("3. Loading CSV ...")
    df = load_raw_csv()
    print(f"   rows: {len(df)}  cols: {df.shape[1]}")
    print("4. Bulk star-schema load (locations/customers/categories/products/orders/items/returns)...")
    bulk_load_star_schema(df)
    print("5. Daily sales aggregate + RandomForest 30-day forecast ...")
    compute_and_load_daily_sales_and_forecast(df)
    print("6. Snapshot KPIs + top products + top customers + recommendations ...")
    compute_and_load_snapshots()
    print("7. Data quality report ...")
    compute_and_load_quality()
    print("\n8. Final row counts:")
    count_all_tables()
    print("\nDone. In Workbench, right-click SCHEMAS -> Refresh All, then open", DB_NAME)
    print("App was also reconfigured (DB_NAME in .env). Restart the backend.")


if __name__ == "__main__":
    main()
