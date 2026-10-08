from __future__ import annotations

import json
import urllib.request

BASE = "http://127.0.0.1:8091"


def req(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode() or "{}")
        except Exception:
            payload = {"error": str(e)}
        return e.code, payload


def main() -> None:
    print("[1] GET /api/health")
    code, data = req("GET", "/api/health")
    print("   ", code, json.dumps(data))
    assert code == 200
    assert data.get("auth_backend") == "mysql", f"Expected mysql, got {data!r}"

    print("\n[2] POST /api/auth/login  demo@example.com / demo-password")
    code, data = req("POST", "/api/auth/login", {"email": "demo@example.com", "password": "demo-password"})
    print("   ", code, json.dumps({k: v for k, v in data.items() if k != "access_token"}))
    assert code == 200, (code, data)
    token = data["access_token"]
    print("    got access_token length:", len(token))

    print("\n[3] GET /api/dashboard/kpis  (with the token)")
    code, data = req("GET", "/api/dashboard/kpis", token=token)
    print("   ", code, "keys:", sorted(data.keys()) if isinstance(data, dict) else type(data).__name__)
    assert code == 200, (code, data)

    print("\n[4] POST /api/auth/register  (new user)")
    new_email = "mysql_test_" + __import__("uuid").uuid4().hex[:8] + "@example.com"
    code, data = req("POST", "/api/auth/register", {"email": new_email, "password": "Abcd@1234", "role": "Analyst"})
    print("   ", code, json.dumps({k: v for k, v in data.items() if k != "access_token"}))
    assert code == 200, (code, data)

    print("\n[5] Verify the new user is in MySQL (re-login as the new user)")
    code, data = req("POST", "/api/auth/login", {"email": new_email, "password": "Abcd@1234"})
    print("   ", code, json.dumps({k: v for k, v in data.items() if k != "access_token"}))
    assert code == 200, (code, data)
    assert data["role"] == "Analyst", data

    print("\n[6] Re-login with the default demo admin after DB round-trip")
    code, data = req("POST", "/api/auth/login", {"email": "demo@example.com", "password": "demo-password"})
    assert code == 200 and data["role"] == "Admin"
    print("   OK:", code, "role=", data["role"])
    print("\nALL CHECKS PASSED — MySQL login persistence works end-to-end.")


if __name__ == "__main__":
    main()
