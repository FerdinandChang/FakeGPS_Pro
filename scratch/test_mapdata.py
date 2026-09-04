import re
import requests

with open("acclist.js", "r", encoding="utf-8") as f:
    code = f.read()

idx = code.find("Handlers/MapData.ashx")
print("Context around MapData.ashx:")
print(code[max(0, idx - 200): min(len(code), idx + 400)])

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://pipimushroom.com/acclist.aspx"
}

# Try GET / POST to MapData.ashx
r1 = requests.get("https://pipimushroom.com/Handlers/MapData.ashx", headers=headers)
print("GET status:", r1.status_code, "text len:", len(r1.text), "preview:", r1.text[:200])

r2 = requests.post("https://pipimushroom.com/Handlers/MapData.ashx", headers=headers, json={"action": "get_all"})
print("POST status:", r2.status_code, "text len:", len(r2.text), "preview:", r2.text[:200])
