"""
Run this AFTER upgrading Firebase to Blaze plan.
It verifies the project can send real SMS.
"""
import json
import urllib.request
import urllib.error

API_KEY = "AIzaSyAEVXdnyvOqL0Uwp0pDKkASV28du5_pU8A"
PHONE = "+916363276441"

print("Testing Firebase Blaze plan SMS capability...")
print(f"Phone: {PHONE}")
print()

url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendVerificationCode?key={API_KEY}"

# recaptchaToken='test' only works for test numbers.
# For real phones: if Blaze is active error becomes INVALID_RECAPTCHA_TOKEN (good)
# If still Spark plan: error is BILLING_NOT_ENABLED (bad)
payload = json.dumps({"phoneNumber": PHONE, "recaptchaToken": "test"}).encode()

req = urllib.request.Request(
    url, data=payload,
    headers={"Content-Type": "application/json"},
)

try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode())
    print("SUCCESS - SMS sent! (Phone is in test number list)")
    print("Response:", data)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    err = json.loads(body).get("error", {})
    error_code = err.get("message", "")
    print(f"Error Code: {error_code}")
    print()
    if error_code == "BILLING_NOT_ENABLED":
        print("RESULT: Firebase project is still on Spark (FREE) plan.")
        print("   Go to Firebase Console, click 'Upgrade', select Blaze plan.")
    elif error_code in ("INVALID_RECAPTCHA_TOKEN", "MISSING_CLIENT_IDENTIFIER", "CAPTCHA_CHECK_FAILED"):
        print("RESULT: Blaze plan is ACTIVE! Real SMS will work from the browser.")
        print("   The browser RecaptchaVerifier handles reCAPTCHA automatically.")
    else:
        print(f"Unknown error: {error_code}")
        print("Full body:", body)
