from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("USE_IN_MEMORY_DB", "0")

from backend.app.database import (  # noqa: E402
    DB_BACKEND,
    build_mysql_url,
    create_user,
    get_session,
    get_user_by_email,
    init_db,
)


def mysql_url_safe() -> str:
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    name = os.getenv("DB_NAME", "ecommerce_intelligence")
    return f"mysql+pymysql://{user}:***@{host}:{port}/{name}"


def main() -> int:
    print("=" * 70)
    print("Nexus Commerce Intelligence — MySQL setup for login persistence")
    print("=" * 70)

    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    db_name = os.getenv("DB_NAME", "ecommerce_intelligence")
    print(f"Target: {mysql_url_safe()}")
    print()

    if DB_BACKEND not in ("mysql",):
        print(f"[!] Database backend detected: {DB_BACKEND!r}")
        print("    -> The backend is NOT using MySQL right now.")
        if DB_BACKEND == "sqlite":
            print("    -> It is using the local SQLite fallback: data/users.db")
        elif DB_BACKEND == "sqlite-memory":
            print("    -> It is using in-memory SQLite (pytest mode).")
        print()
        print("Most common causes:")
        print("  1. DB_PASSWORD in .env is empty or wrong.")
        print("  2. MySQL service isn't running (Services -> MySQL80 -> Start).")
        print("  3. DB_USER in .env is a user that doesn't exist in MySQL.")
        print("  4. Root user has auth_socket / caching_sha2_password and PyMySQL can't log in.")
        print()
        try:
            import pymysql  # noqa: F401
        except ImportError:
            print("[!] PyMySQL package not installed. Run: .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
            return 3
        return 2

    print("[+] MySQL connection successful — backend is using MySQL.")
    print(f"    host={host}  port={port}  user={user}  database={db_name}")
    print()

    init_db()
    print("[+] Database + users table ready.")

    from backend.app.main import hash_password  # noqa: E402

    admin_email = os.getenv("ADMIN_EMAIL", "demo@example.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "demo-password")

    with get_session() as session:
        existing = get_user_by_email(session, admin_email)
        if existing:
            print(f"[=] Admin user already exists: {admin_email}  role={existing.role or 'Viewer'}")
        else:
            create_user(session, admin_email, hash_password(admin_password), "Admin")
            print(f"[+] Seeded Admin user: {admin_email}")

        demo_email = "demo@example.com"
        if admin_email != demo_email:
            existing_demo = get_user_by_email(session, demo_email)
            if existing_demo:
                print(f"[=] Demo user already exists: {demo_email}  role={existing_demo.role or 'Viewer'}")
            else:
                create_user(session, demo_email, hash_password("demo-password"), "Admin")
                print(f"[+] Seeded Demo user: {demo_email}")

        count_q = session.execute(
            __import__("sqlalchemy").text("SELECT COUNT(*) FROM users")
        ).scalar_one()
        print(f"[+] Total registered users in MySQL: {count_q}")
        rows = session.execute(
            __import__("sqlalchemy").text(
                "SELECT id, email, role, created_at FROM users ORDER BY id"
            )
        ).all()
        for row in rows:
            print(f"     {row.id:>4}  {row.role or 'Viewer':<18}  {row.email:<36}  created={row.created_at}")

    print()
    print("[i] Start the backend and visit:  http://127.0.0.1:8000/api/health")
    print("    It should report  auth_backend: 'mysql'")
    print()
    print("[i] In MySQL Workbench, run:")
    print("    USE ecommerce_intelligence;")
    print("    SELECT id, email, role, created_at FROM users;")
    return 0


if __name__ == "__main__":
    sys.exit(main())
