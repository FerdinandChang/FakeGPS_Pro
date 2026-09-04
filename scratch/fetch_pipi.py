import requests
import json
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

r = requests.get("https://pipimushroom.com/acclist.aspx", headers=headers)
print("Status:", r.status_code)
html = r.text

# Find scripts
scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
print("Scripts:", scripts)

# Find any inline json / data or API endpoints
api_urls = re.findall(r'https?://[^\s"\']+(?:\.json|\.aspx|\.ashx|\.php|/api/[^\s"\']+)', html)
print("API URLs in HTML:", api_urls)

# Also check for inline tables or data
if "table" in html.lower():
    print("Table present in HTML")

# Check if there is data embedded in script tags
embedded_data = re.findall(r'(?:var|let|const)\s+([a-zA-Z0-9_]+)\s*=\s*(\[.*?\]|\{.*?\});', html, re.DOTALL)
for var_name, val in embedded_data:
    if len(val) > 100:
        print(f"Found embedded data: {var_name} (len={len(val)})")

with open("pipimushroom.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved pipimushroom.html (len={})".format(len(html)))
