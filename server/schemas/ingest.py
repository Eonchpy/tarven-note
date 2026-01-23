from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestEntity(BaseModel):
    type: str
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestRelationship(BaseModel):
    from_entity_name: str
    to_entity_name: str
    type: str
    bidirectional: bool = False
    reverse_type: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    entities: List[IngestEntity]
    relationships: List[IngestRelationship]


class IngestResponse(BaseModel):
    entities_count: int
    relationships_count: int
