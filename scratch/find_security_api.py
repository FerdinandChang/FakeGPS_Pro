import re

with open("api_security.js", "r", encoding="utf-8") as f:
    sec_code = f.read()

# Look for window properties
window_props = re.findall(r'window\[[\'"]([^\'"]+)[\'"]\]\s*=', sec_code)
print("window props in api_security.js:", window_props)

with open("acclist.js", "r", encoding="utf-8") as f:
    acc_code = f.read()

window_calls = re.findall(r'window\[[\'"]([^\'"]+)[\'"]\]', acc_code)
print("window props in acclist.js:", set(window_calls))
