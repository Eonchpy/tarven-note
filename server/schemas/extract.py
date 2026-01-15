from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    content: str
    speaker: Optional[str] = None
    timestamp: Optional[datetime] = None


class ExtractedEntity(BaseModel):
    type: str
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedRelationship(BaseModel):
    from_entity_name: str
    to_entity_name: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class ExtractResponse(BaseModel):
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]
