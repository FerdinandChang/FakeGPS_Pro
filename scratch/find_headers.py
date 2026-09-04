with open("api_security.js", "r", encoding="utf-8") as f:
    code = f.read()

idx = code.find("headers")
while idx != -1:
    print("Found headers at:", idx)
    print(code[max(0, idx - 100): min(len(code), idx + 200)])
    print("=" * 60)
    idx = code.find("headers", idx + 1)
