import re

with open("pipimushroom.html", "r", encoding="utf-8") as f:
    html = f.read()

tokens = re.findall(r'token|auth|key|secret', html, re.IGNORECASE)
print("tokens in html:", tokens)

# Look for meta tags or script tags with token
meta_tags = re.findall(r'<meta[^>]+>', html)
print("meta tags:", meta_tags)

with open("acclist.js", "r", encoding="utf-8") as f:
    js = f.read()

# Look for 'Missing API token' or token headers in js
token_matches = re.findall(r'[^a-zA-Z0-9_]token[^a-zA-Z0-9_]', js, re.IGNORECASE)
print("token matches in js count:", len(token_matches))
