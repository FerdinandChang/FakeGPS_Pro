"""
FakeGPS Pro - Application Version Definition
"""
CURRENT_VERSION = "1.0.0"

def parse_version(ver_str: str):
    """解析版本字串為數字元組，例如 'v1.2.3' -> (1, 2, 3)"""
    cleaned = str(ver_str).strip().lower().lstrip("v")
    parts = []
    for p in cleaned.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def is_newer_version(remote_ver: str, local_ver: str = CURRENT_VERSION) -> bool:
    """判斷遠端版本是否比本地版本更新"""
    return parse_version(remote_ver) > parse_version(local_ver)
