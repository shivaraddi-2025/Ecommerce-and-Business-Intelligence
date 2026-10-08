"""
Test if Firebase Phone Auth (Blaze plan) can now send real SMS OTP.
"""
import json
import urllib.request
import urllib.error

API_KEY = "AIzaSyAEVXdnyvOqL0Uwp0pDKkASV28du5_pU8A"
PHONE = "+916363276441"

url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendVerificationCode?key={API_KEY}"
payload = json.dumps({"phoneNumber": PHONE, "recaptchaToken": "test"}).encode()

req = urllib.request.Request(
    url,
    data=payload,
    headers={"Content-Type": "application/json"},
)

try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode())
    print("SUCCESS - Firebase sent OTP! Response:", data)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    err = json.loads(body).get("error", {})
    print("Status Code :", e.code)
    print("Error Code  :", err.get("message", ""))
    print("Full Body   :", body)
