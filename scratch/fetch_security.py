import requests
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://pipimushroom.com/acclist.aspx"
}

r = requests.get("https://pipimushroom.com/Scripts/dist/api-security.min.js", headers=headers)
print("api-security status:", r.status_code, "len:", len(r.text))

with open("api_security.js", "w", encoding="utf-8") as f:
    f.write(r.text)

print("Preview of api_security.js:")
print(r.text[:500])
