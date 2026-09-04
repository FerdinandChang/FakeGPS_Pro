import requests
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

r = requests.get("https://pipimushroom.com/Scripts/dist/acclist.min.js", headers=headers)
print("acclist.min.js status:", r.status_code, "len:", len(r.text))

# Search for fetch / ajax / endpoints in the JS
urls = re.findall(r'["\'](/[^"\']+\.(?:ashx|aspx|json|php|api)[^"\']*)["\']', r.text)
print("Relative endpoints:", urls)

# Search for all strings matching api or data
all_paths = re.findall(r'["\'](/[a-zA-Z0-9_\-\./]+)["\']', r.text)
print("All paths:", all_paths[:20])

with open("acclist.js", "w", encoding="utf-8") as f:
    f.write(r.text)
