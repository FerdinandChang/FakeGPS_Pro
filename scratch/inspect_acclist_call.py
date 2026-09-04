with open("acclist.js", "r", encoding="utf-8") as f:
    code = f.read()

idx = 0
while True:
    idx = code.find("PikminApi", idx)
    if idx == -1:
        break
    print(f"Match in acclist at {idx}:")
    print(code[max(0, idx - 100): min(len(code), idx + 300)])
    print("-" * 50)
    idx += len("PikminApi")
