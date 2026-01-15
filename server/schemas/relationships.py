from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RelationshipCreate(BaseModel):
    from_entity_id: str
    to_entity_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class RelationshipResponse(BaseModel):
    relationship_id: str
    from_entity_id: str
    to_entity_id: str
    type: str
    properties: Dict[str, Any]


class RelationshipListFilters(BaseModel):
    from_entity_id: Optional[str] = None
    to_entity_id: Optional[str] = None
    type: Optional[str] = None
