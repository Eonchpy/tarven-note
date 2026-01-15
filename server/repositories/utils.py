import json
import re
from typing import Any, Dict, Iterable


LABEL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def normalize_label(value: str, prefix: str, upper: bool = False) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
    cleaned = cleaned.strip("_")
    if upper:
        cleaned = cleaned.upper()
    if not cleaned:
        cleaned = prefix
    if not LABEL_PATTERN.match(cleaned):
        cleaned = f"{prefix}_{cleaned}"
    return cleaned


def serialize_map(value: Any) -> str:
    if value is None:
        return json.dumps({})
    if isinstance(value, str):
        return value
    return json.dumps(value)


def deserialize_map(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


def _normalize_datetime(value: Any) -> Any:
    if hasattr(value, "to_native"):
        return value.to_native()
    return value


def node_to_dict(node: Any, map_fields: Iterable[str]) -> Dict[str, Any]:
    data = dict(node)
    for field in map_fields:
        if field in data:
            data[field] = deserialize_map(data[field])
    for field in ("created_at", "updated_at"):
        if field in data:
            data[field] = _normalize_datetime(data[field])
    return data


def relationship_to_dict(rel: Any, map_fields: Iterable[str]) -> Dict[str, Any]:
    data = dict(rel)
    for field in map_fields:
        if field in data:
            data[field] = deserialize_map(data[field])
    for field in ("created_at", "updated_at"):
        if field in data:
            data[field] = _normalize_datetime(data[field])
    return data
