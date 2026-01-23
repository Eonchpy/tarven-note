"""
Entity attribute schema definitions.
定义各类型实体的固定属性key，用于schema enforcement。
"""
from typing import Any, Dict, Set


# 通用属性 - 所有类型共享
COMMON_FIELDS: Set[str] = {
    "description",
}

# 列表类型字段 - 追加而非覆盖
LIST_FIELDS: Set[str] = {
    "aliases",
    "used_names",
    "notes",
}

# Character 类型属性
CHARACTER_FIELDS: Set[str] = {
    "occupation",
    "age",
    "gender",
    "appearance",
    "personality",
    "background",
}

# Location 类型属性
LOCATION_FIELDS: Set[str] = {
    "location_type",
    "address",
}

# Item 类型属性
ITEM_FIELDS: Set[str] = {
    "item_type",
    "rarity",
}

# Event 类型属性
EVENT_FIELDS: Set[str] = {
    "event_time",
    "participants",
}

# Organization 类型属性
ORGANIZATION_FIELDS: Set[str] = {
    "org_type",
    "members",
}

# attributes 字段内部的固定key（规则系统属性）
# 一级key钉死，二级key（具体属性名/技能名）可灵活
ATTRIBUTES_KEYS: Set[str] = {
    "stats",      # 基础属性 {"STR": 50, "CON": 60, ...}
    "skills",     # 技能值 {"侦查": 60, "图书馆使用": 40, ...}
    "hp",         # 生命值
    "mp",         # 魔法值
    "san",        # 理智值 (COC)
    "luck",       # 幸运值
    "level",      # 等级 (DND)
    "class",      # 职业 (DND)
    "race",       # 种族
    "ext",        # 扩展字段，兜底
}

# 类型 → 允许的字段映射
TYPE_FIELDS_MAP: Dict[str, Set[str]] = {
    "Character": CHARACTER_FIELDS,
    "Location": LOCATION_FIELDS,
    "Item": ITEM_FIELDS,
    "Event": EVENT_FIELDS,
    "Organization": ORGANIZATION_FIELDS,
    "Clue": set(),
    "Skill": set(),
    "Unknown": set(),
}


def get_allowed_fields(entity_type: str) -> Set[str]:
    """获取指定类型允许的所有字段"""
    type_fields = TYPE_FIELDS_MAP.get(entity_type, set())
    return COMMON_FIELDS | LIST_FIELDS | type_fields | {"attributes"}


def filter_properties(
    entity_type: str,
    properties: Dict[str, Any]
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    过滤属性，分离为：已知字段 + 扩展字段(attributes)
    返回: (known_fields, ext_fields)
    """
    allowed = get_allowed_fields(entity_type)
    known = {}
    ext = {}

    for key, value in properties.items():
        if key in allowed:
            known[key] = value
        else:
            ext[key] = value

    return known, ext
