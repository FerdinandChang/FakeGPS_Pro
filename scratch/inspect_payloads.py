with open("acclist.js", "r", encoding="utf-8") as f:
    code = f.read()

# Let's deobfuscate or look around the function that calls _0x52bce7
idx = code.find("_0x52bce7")
while idx != -1:
    print(f"Calling _0x52bce7 at {idx}:")
    print(code[max(0, idx - 100): min(len(code), idx + 200)])
    print("=" * 60)
    idx = code.find("_0x52bce7", idx + 1)
