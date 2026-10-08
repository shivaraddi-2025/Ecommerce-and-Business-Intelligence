"""
Configure Firebase Test Phone Numbers.
Test phone numbers bypass SMS billing and work on the FREE Spark plan.
Firebase validates them as real phone auth sessions (issues real ID tokens).
"""
import json
import urllib.request
import urllib.error
import google.oauth2.service_account
from google.auth.transport.requests import Request

KEY_FILE = 'firebase-adminsdk-e-commerce-and-intelligence.json'
creds = google.oauth2.service_account.Credentials.from_service_account_file(
    KEY_FILE,
    scopes=[
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/firebase',
    ],
)
req = Request()
creds.refresh(req)
token = creds.token

project_id = 'e-commerce-and-intelligence'

# ---- 1. Read current config ----
url_get = f'https://identitytoolkit.googleapis.com/admin/v2/projects/{project_id}/config'
r_get = urllib.request.Request(url_get, headers={'Authorization': f'Bearer {token}'})
resp_get = urllib.request.urlopen(r_get, timeout=10)
current = json.loads(resp_get.read().decode())
existing_tests = current.get('signIn', {}).get('phoneNumber', {}).get('testPhoneNumbers', {})
print("Existing test numbers:", existing_tests)

# ---- 2. Add test phone numbers ----
# These numbers bypass SMS and work completely free on the Spark plan.
# Any employee phone number you want to test can be added here.
test_numbers = {
    "+916363276441": "123456",   # Your mobile  — OTP is 123456
    "+919876543210": "123456",   # Already existed
    "+919000000001": "654321",   # Generic test — OTP is 654321
    "+919000000002": "000000",   # Generic test — OTP is 000000
    "+919000000003": "888888",   # Generic test — OTP is 888888
}
# Merge with existing so we don't wipe others
merged = {**existing_tests, **test_numbers}

url_patch = (
    f'https://identitytoolkit.googleapis.com/admin/v2/projects/{project_id}/config'
    f'?updateMask=signIn.phoneNumber.testPhoneNumbers'
)
payload = {'signIn': {'phoneNumber': {'testPhoneNumbers': merged}}}
data = json.dumps(payload).encode()
r_patch = urllib.request.Request(
    url_patch, data=data,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    method='PATCH',
)
try:
    resp = urllib.request.urlopen(r_patch, timeout=10)
    result = json.loads(resp.read().decode())
    print("\n✅ Test phone numbers set successfully!")
    print("Active test numbers:", json.dumps(
        result.get('signIn', {}).get('phoneNumber', {}).get('testPhoneNumbers', {}),
        indent=2
    ))
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode())
