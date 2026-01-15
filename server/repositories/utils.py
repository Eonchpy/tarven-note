import re


LABEL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def normalize_label(value: str) -> str:
    cleaned = value.strip()
    if not LABEL_PATTERN.match(cleaned):
        raise ValueError("Invalid label")
    return cleaned
