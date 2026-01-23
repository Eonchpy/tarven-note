"""
SQLite message repository for tarven-note.
提供对话消息的存储操作，用于双路召回。
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from server.db.sqlite import get_cursor


def store_message(
    campaign_id: str,
    role: str,
    content: str,
    entity_ids: Optional[List[str]] = None,
) -> str:
    """存储对话消息，返回message_id"""
    message_id = str(uuid4())
    now = datetime.utcnow().isoformat()
    entity_ids_json = json.dumps(entity_ids) if entity_ids else None

    with get_cursor() as cursor:
        cursor.execute(
            """INSERT INTO messages
               (message_id, campaign_id, role, content, entity_ids, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (message_id, campaign_id, role, content, entity_ids_json, now)
        )
    return message_id


def get_recent_messages(
    campaign_id: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """获取最近的消息"""
    with get_cursor() as cursor:
        cursor.execute(
            """SELECT * FROM messages
               WHERE campaign_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (campaign_id, limit)
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]
