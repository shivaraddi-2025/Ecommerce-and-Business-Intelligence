from __future__ import annotations

import pymysql

PASSWORD = "MySQL@2026"


def main() -> None:
    print("--- STEP 1. Check for mysql.infoschema system user + create if missing (connect NO DB) ---")
    conn2 = pymysql.connect(
        host="127.0.0.1", port=3306, user="root", password=PASSWORD,
        charset="utf8mb4",
    )
    cur2 = conn2.cursor()
    try:
        cur2.execute('SELECT user, host FROM mysql.user WHERE user IN ("mysql.infoschema","mysql.session","mysql.sys")')
        rows = cur2.fetchall()
        print("system users found:", rows)
        if not any(r[0] == "mysql.infoschema" for r in rows):
            print("CREATING mysql.infoschema user ...")
            cur2.execute(
                "CREATE USER IF NOT EXISTS `mysql.infoschema`@`localhost` "
                "IDENTIFIED WITH caching_sha2_password "
                "AS '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED'"
            )
            cur2.execute("GRANT SELECT, SHOW VIEW ON *.* TO `mysql.infoschema`@`localhost`")
            try:
                cur2.execute("GRANT SYSTEM_USER ON *.* TO `mysql.infoschema`@`localhost`")
            except Exception as e:
                print("(note) SYSTEM_USER grant skipped:", e)
            cur2.execute("FLUSH PRIVILEGES")
            print("OK: created mysql.infoschema")
        else:
            print("OK: mysql.infoschema user exists")

        print("\n--- STEP 1b. Check information_schema views are now usable ---")
        cur2.execute("SELECT COUNT(*) FROM information_schema.SCHEMATA")
        print("SCHEMATA rows:", cur2.fetchone()[0])
        cur2.execute("SELECT COUNT(*) FROM information_schema.TABLES")
        print("TABLES rows:", cur2.fetchone()[0])
        cur2.execute("SELECT COUNT(*) FROM information_schema.COLUMNS")
        print("COLUMNS rows:", cur2.fetchone()[0])
    except Exception as e:
        print("repair step FAILED:", type(e).__name__, e)
    finally:
        cur2.close()
        conn2.close()

    print("\n--- STEP 2. SHOW TABLES in ecommerce_intelligence ---")
    conn = pymysql.connect(
        host="127.0.0.1", port=3306, user="root", password=PASSWORD,
        charset="utf8mb4", database="ecommerce_intelligence",
    )
    cur = conn.cursor()
    try:
        cur.execute("SHOW TABLES")
        print(cur.fetchall())
    except Exception as e:
        print("SHOW TABLES FAILED:", type(e).__name__, e)

    print("\n--- STEP 3. SELECT from users ---")
    try:
        cur.execute("SELECT id, email, role FROM users")
        print(cur.fetchall())
    except Exception as e:
        print("FAILED:", type(e).__name__, e)
    cur.close()
    conn.close()

    print("\n--- STEP 4. Retry DESCRIBE users ---")
    conn3 = pymysql.connect(
        host="127.0.0.1", port=3306, user="root", password=PASSWORD,
        charset="utf8mb4", database="ecommerce_intelligence",
    )
    cur3 = conn3.cursor()
    try:
        cur3.execute("DESCRIBE `ecommerce_intelligence`.`users`")
        rows = cur3.fetchall()
        print("DESCRIBE OK:")
        for r in rows:
            print("  ", r)
    except Exception as e:
        print("DESCRIBE FAILED:", type(e).__name__, e)
    cur3.close()
    conn3.close()


if __name__ == "__main__":
    main()
