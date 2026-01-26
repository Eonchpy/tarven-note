from fastapi import APIRouter, HTTPException

from server.repositories.campaigns import (
    create_campaign,
    delete_campaign,
    get_campaign,
    list_campaigns,
    update_campaign,
)
from server.schemas.campaigns import CampaignCreate, CampaignResponse, CampaignUpdate

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse)
async def create_campaign_handler(payload: CampaignCreate):
    campaign = create_campaign(
        payload.name,
        payload.system,
        payload.description,
        payload.metadata,
        payload.campaign_id,
    )
    return campaign


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns_handler():
    return list_campaigns()


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign_handler(campaign_id: str):
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign_handler(campaign_id: str, payload: CampaignUpdate):
    updates = payload.model_dump(exclude_unset=True)
    campaign = update_campaign(campaign_id, updates)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign_handler(campaign_id: str):
    deleted = delete_campaign(campaign_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "deleted"}
