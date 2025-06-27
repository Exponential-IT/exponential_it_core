from typing import Optional


def normalize_empty_string(v: Optional[str]) -> Optional[str]:
    return None if isinstance(v, str) and not v.strip() else v
