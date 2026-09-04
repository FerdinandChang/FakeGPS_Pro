import hmac
import hashlib
import json
import time
import requests
import base64

# Let's inspect the keys from api-security.js
# In api-security:
# Keys are derived from array of strings joined by ','
# Let's check how api_security generates the signature.

W = [f"W{i}" for i in range(1, 33)]
X = [f"X{i}" for i in range(1, 33)]
Y = [f"Y{i}" for i in range(1, 33)]
Z = [f"Z{i}" for i in range(1, 33)]
K = [f"K{i}" for i in range(1, 33)]

def hmac_sha256(key_str, msg_str):
    key = key_str.encode('utf-8')
    msg = msg_str.encode('utf-8')
    sig = hmac.new(key, msg, hashlib.sha256).digest()
    return base64.b64encode(sig).decode('utf-8')

def get_signature(url_path, payload_dict, timestamp_str):
    body_str = json.dumps(payload_dict, separators=(',', ':'), ensure_ascii=False)
    raw_str = f"{url_path}:{timestamp_str}:{body_str}"
    
    # 5 rounds of HMAC
    key_groups = [W, X, Y, Z, K]
    signatures = []
    for grp in key_groups:
        k_str = ",".join(grp)
        sig = hmac_sha256(k_str, raw_str)
        signatures.append(sig)
    
    signatures.append(timestamp_str)
    return ".".join(signatures)

# Test requesting MapData.ashx
payload = {"mode": "filters", "region": "TW"}
ts = str(int(time.time() * 1000))
sig = get_signature("Handlers/MapData.ashx", payload, ts)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "X-API-Time": ts,
    "X-API-Signature": sig,
    "Referer": "https://pipimushroom.com/acclist.aspx"
}

resp = requests.post("https://pipimushroom.com/Handlers/MapData.ashx", headers=headers, data=json.dumps(payload, separators=(',', ':'), ensure_ascii=False))
print("Status:", resp.status_code)
print("Response text len:", len(resp.text))
print("Response preview:", resp.text[:300])
