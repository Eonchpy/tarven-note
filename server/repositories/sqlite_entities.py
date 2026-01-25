"""
SQLite entity repository for tarven-note.
提供实体的SQLite存储操作。
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from server.db.sqlite import get_cursor

logger = logging.getLogger(__name__)
from server.schemas.entity_attributes import LIST_FIELDS, ATTRIBUTES_KEYS

# 实体表的所有列名
ENTITY_COLUMNS = {
    "description", "occupation", "age", "gender", "appearance",
    "personality", "background", "location_type", "address",
    "item_type", "rarity", "event_time", "participants",
    "org_type", "members", "attributes", "aliases", "used_names",
    "notes", "metadata",
}

# JSON类型的列
JSON_COLUMNS = {
    "participants", "members", "attributes",
    "aliases", "used_names", "notes", "metadata",
}


def _to_json(value: Any) -> Optional[str]:
    """转换为JSON字符串"""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _merge_list(old_json: Optional[str], new_val: Any) -> str:
    """合并列表字段"""
    old = json.loads(old_json) if old_json else []
    if isinstance(new_val, list):
        old.extend(new_val)
    elif new_val:
        old.append(new_val)
    return json.dumps(old, ensure_ascii=False)


def _sync_aliases(cursor, campaign_id: str, entity_id: str, aliases: List[str]) -> None:
    """同步别名到 entity_aliases 表"""
    for alias in aliases:
        cursor.execute(
            """INSERT OR IGNORE INTO entity_aliases
               (campaign_id, entity_id, alias) VALUES (?, ?, ?)""",
            (campaign_id, entity_id, alias)
        )


def upsert_entity(
    entity_id: str,
    campaign_id: str,
    entity_type: str,
    name: str,
    properties: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """插入或更新实体"""
    now = datetime.utcnow().isoformat()

    with get_cursor() as cursor:
        # 查询是否存在
        cursor.execute(
            "SELECT * FROM entities WHERE campaign_id = ? AND name = ?",
            (campaign_id, name)
        )
        existing = cursor.fetchone()

        if not existing:
            # INSERT 新记录
            cols = ["entity_id", "campaign_id", "type", "name", "created_at", "updated_at"]
            vals = [entity_id, campaign_id, entity_type, name, now, now]

            for key, val in properties.items():
                if key in ENTITY_COLUMNS:
                    cols.append(key)
                    vals.append(_to_json(val) if key in JSON_COLUMNS else val)

            if metadata:
                cols.append("metadata")
                vals.append(_to_json(metadata))

            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            cursor.execute(f"INSERT INTO entities ({col_names}) VALUES ({placeholders})", vals)

            # 同步别名
            if "aliases" in properties:
                aliases = properties["aliases"]
                if isinstance(aliases, list):
                    _sync_aliases(cursor, campaign_id, entity_id, aliases)

        else:
            # UPDATE 现有记录
            updates = ["updated_at = ?"]
            vals = [now]

            # 如果当前type是Unknown，允许更新type
            if existing["type"] == "Unknown" and entity_type != "Unknown":
                updates.append("type = ?")
                vals.append(entity_type)

            for key, val in properties.items():
                if key not in ENTITY_COLUMNS:
                    continue

                if key in LIST_FIELDS:
                    # 列表字段：追加
                    merged = _merge_list(existing[key], val)
                    updates.append(f"{key} = ?")
                    vals.append(merged)
                else:
                    # 普通字段：覆盖
                    updates.append(f"{key} = ?")
                    vals.append(_to_json(val) if key in JSON_COLUMNS else val)

            set_clause = ", ".join(updates)
            vals.extend([campaign_id, name])
            cursor.execute(
                f"UPDATE entities SET {set_clause} WHERE campaign_id = ? AND name = ?",
                vals
            )

            # 同步别名
            if "aliases" in properties:
                aliases = properties["aliases"]
                if isinstance(aliases, list):
                    _sync_aliases(cursor, campaign_id, existing["entity_id"], aliases)


def get_entities_by_names(campaign_id: str, names: List[str]) -> Dict[str, Dict[str, Any]]:
    """批量根据名称获取实体，返回 {name: entity_data} 字典"""
    if not names:
        return {}
    with get_cursor() as cursor:
        placeholders = ", ".join(["?"] * len(names))
        cursor.execute(
            f"SELECT * FROM entities WHERE campaign_id = ? AND name IN ({placeholders})",
            [campaign_id] + names
        )
        rows = cursor.fetchall()
        result = {}
        for row in rows:
            entity = dict(row)
            for key in JSON_COLUMNS:
                if key in entity and entity[key]:
                    try:
                        entity[key] = json.loads(entity[key])
                    except (json.JSONDecodeError, TypeError):
                        pass
            result[entity["name"]] = entity
        return result


def get_entity_by_name(campaign_id: str, name: str) -> Optional[Dict[str, Any]]:
    """根据名称获取实体"""
    logger.info(f"get_entity_by_name: campaign_id={campaign_id}, name={name}")
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM entities WHERE campaign_id = ? AND name = ?",
            (campaign_id, name)
        )
        row = cursor.fetchone()
        if not row:
            logger.warning(f"get_entity_by_name: No row found for campaign_id={campaign_id}, name={name}")
            # 调试：列出该campaign的所有实体
            cursor.execute("SELECT name FROM entities WHERE campaign_id = ?", (campaign_id,))
            all_names = [r[0] for r in cursor.fetchall()]
            logger.info(f"get_entity_by_name: All names in campaign: {all_names}")
            return None
        result = dict(row)
        logger.info(f"get_entity_by_name: Found row, keys={list(result.keys())}")
        # 解析JSON字段
        for key in JSON_COLUMNS:
            if key in result and result[key]:
                try:
                    result[key] = json.loads(result[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return result
