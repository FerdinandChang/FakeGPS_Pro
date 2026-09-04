import re

with open("api_security.js", "r", encoding="utf-8") as f:
    code = f.read()

# find where PikminApi is defined or assigned
idx = 0
while True:
    idx = code.find("PikminApi", idx)
    if idx == -1:
        break
    print(f"Match at {idx}:")
    print(code[max(0, idx - 100): min(len(code), idx + 200)])
    print("-" * 50)
    idx += len("PikminApi")
