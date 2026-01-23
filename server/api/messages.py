"""
Message API endpoints for tarven-note.
"""
from fastapi import APIRouter
from typing import List, Dict, Any

from server.repositories.sqlite_messages import store_message, get_recent_messages
from server.schemas.messages import MessageCreate

router = APIRouter(prefix="/api/campaigns/{campaign_id}/messages", tags=["messages"])


@router.post("")
async def create_message(campaign_id: str, payload: MessageCreate):
    """存储对话消息"""
    message_id = store_message(
        campaign_id=campaign_id,
        role=payload.role,
        content=payload.content,
        entity_ids=payload.entity_ids,
    )
    return {"message_id": message_id}


@router.get("")
async def list_messages(campaign_id: str, limit: int = 10):
    """获取最近的消息"""
    messages = get_recent_messages(campaign_id, limit)
    return {"messages": messages}
