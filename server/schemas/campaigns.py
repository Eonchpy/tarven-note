from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str
    system: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    system: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CampaignResponse(BaseModel):
    campaign_id: str
    name: str
    system: str
    description: Optional[str]
    status: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
