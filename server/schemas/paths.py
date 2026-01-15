from typing import List

from pydantic import BaseModel


class PathResponse(BaseModel):
    nodes: List[str]
    relationships: List[str]
    hops: int


class PathsResponse(BaseModel):
    paths: List[PathResponse]
