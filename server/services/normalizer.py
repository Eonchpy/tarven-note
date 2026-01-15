"""Type normalization for entities and relationships (Layer 2 defense)"""

import logging

logger = logging.getLogger(__name__)

# Entity type mapping (variants -> standard)
ENTITY_TYPE_MAPPING = {
    # Chinese -> English
    "角色": "Character",
    "人物": "Character",
    "地点": "Location",
    "地方": "Location",
    "事件": "Event",
    "线索": "Clue",
    "物品": "Item",
    "道具": "Item",
    "组织": "Organization",
    # Lowercase -> Standard
    "character": "Character",
    "location": "Location",
    "event": "Event",
    "clue": "Clue",
    "item": "Item",
    "organization": "Organization",
}

# Valid entity types
VALID_ENTITY_TYPES = {"Character", "Location", "Event", "Clue", "Item", "Organization"}

# Relationship type mapping
RELATIONSHIP_TYPE_MAPPING = {
    # Chinese -> English
    "认识": "KNOWS",
    "知道": "KNOWS",
    "信任": "TRUSTS",
    "恐惧": "FEARS",
    "害怕": "FEARS",
    "爱": "LOVES",
    "恨": "HATES",
    "位于": "LOCATED_AT",
    "在": "LOCATED_AT",
    "工作于": "WORKS_AT",
    "居住于": "LIVES_AT",
    "住在": "LIVES_AT",
    "参与": "PARTICIPATED_IN",
    "目击": "WITNESSED",
    "导致": "CAUSED",
    "拥有": "OWNS",
    "持有": "OWNS",
    "使用": "USED",
    "发现": "FOUND",
    "属于": "BELONGS_TO",
    "连接": "CONNECTED_TO",
    # Lowercase -> Standard
    "knows": "KNOWS",
    "trusts": "TRUSTS",
    "fears": "FEARS",
    "loves": "LOVES",
    "hates": "HATES",
    "located_at": "LOCATED_AT",
    "works_at": "WORKS_AT",
    "lives_at": "LIVES_AT",
    "participated_in": "PARTICIPATED_IN",
    "witnessed": "WITNESSED",
    "caused": "CAUSED",
    "owns": "OWNS",
    "used": "USED",
    "found": "FOUND",
    "belongs_to": "BELONGS_TO",
    "connected_to": "CONNECTED_TO",
}

# Valid relationship types
VALID_RELATIONSHIP_TYPES = {
    "KNOWS", "TRUSTS", "FEARS", "LOVES", "HATES",
    "LOCATED_AT", "WORKS_AT", "LIVES_AT",
    "PARTICIPATED_IN", "WITNESSED", "CAUSED",
    "OWNS", "USED", "FOUND", "BELONGS_TO", "CONNECTED_TO",
}


def normalize_entity_type(entity_type: str) -> str:
    """Normalize entity type to standard value"""
    original = entity_type

    # Try mapping first
    if entity_type in ENTITY_TYPE_MAPPING:
        entity_type = ENTITY_TYPE_MAPPING[entity_type]

    # Validate
    if entity_type not in VALID_ENTITY_TYPES:
        logger.warning(f"Unknown entity type: {original}, defaulting to 'Character'")
        entity_type = "Character"
    elif entity_type != original:
        logger.info(f"Normalized entity type: {original} -> {entity_type}")

    return entity_type


def normalize_relationship_type(rel_type: str) -> str:
    """Normalize relationship type to standard value"""
    original = rel_type

    # Try mapping first
    if rel_type in RELATIONSHIP_TYPE_MAPPING:
        rel_type = RELATIONSHIP_TYPE_MAPPING[rel_type]

    # Validate
    if rel_type not in VALID_RELATIONSHIP_TYPES:
        logger.warning(f"Unknown relationship type: {original}, defaulting to 'KNOWS'")
        rel_type = "KNOWS"
    elif rel_type != original:
        logger.info(f"Normalized relationship type: {original} -> {rel_type}")

    return rel_type
