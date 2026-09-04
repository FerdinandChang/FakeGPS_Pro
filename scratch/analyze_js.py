import re

with open("acclist.js", "r", encoding="utf-8") as f:
    code = f.read()

# Search for fetch, axios, $.ajax, XMLHttpRequest, url, endpoints
fetches = re.findall(r'fetch\([^\)]+\)', code)
print("fetch calls:", fetches)

# Search for any string with http, /, .ashx, .aspx, api
strings = re.findall(r'["\']([^"\']{4,80})["\']', code)
endpoints = [s for s in strings if any(k in s.lower() for k in ['api', 'acc', 'data', 'spot', 'get', 'list', '.ashx', '.aspx', 'json'])]
print("Matching strings:", endpoints[:30])
