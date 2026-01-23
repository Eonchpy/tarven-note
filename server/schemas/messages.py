"""
Message schemas for tarven-note.
"""
from typing import List, Optional
from pydantic import BaseModel


class MessageCreate(BaseModel):
    role: str
    content: str
    entity_ids: Optional[List[str]] = None
