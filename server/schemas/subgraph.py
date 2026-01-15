from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SubgraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class SubgraphEdge(BaseModel):
    id: str
    from_id: str
    to_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class SubgraphResponse(BaseModel):
    nodes: List[SubgraphNode]
    edges: List[SubgraphEdge]
