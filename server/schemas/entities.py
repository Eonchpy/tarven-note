from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    type: str
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class EntityResponse(BaseModel):
    entity_id: str
    type: str
    name: str
    properties: Dict[str, Any]
    metadata: Dict[str, Any]
