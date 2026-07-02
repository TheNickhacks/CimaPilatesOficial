import re


def normalize_rut(value: str) -> str:
    cleaned = re.sub(r"[^0-9kK]", "", value or "").upper()
    if len(cleaned) < 2:
        raise ValueError("Ingresa un RUT valido.")
    return f"{cleaned[:-1]}-{cleaned[-1]}"

