from fastapi import APIRouter, HTTPException

from server.repositories.entities import create_entity, get_entity_by_name
from server.repositories.relationships import create_relationship
from server.schemas.extract import ExtractRequest, ExtractResponse
from server.services.llm import extract_entities

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["extract"])


@router.post("/extract", response_model=ExtractResponse)
async def extract_handler(campaign_id: str, payload: ExtractRequest):
    extraction = await extract_entities(payload)
    if extraction is None:
        raise HTTPException(status_code=501, detail="LLM extraction not configured")

    entity_map: dict[str, str] = {}

    for entity in extraction.entities:
        created = create_entity(
            campaign_id,
            entity.type,
            entity.name,
            entity.properties,
            entity.metadata,
        )
        entity_map[created["name"]] = created["entity_id"]

    def resolve_entity_id(name: str) -> str:
        if name in entity_map:
            return entity_map[name]
        existing = get_entity_by_name(campaign_id, name)
        if existing:
            entity_map[name] = existing["entity_id"]
            return existing["entity_id"]
        created = create_entity(campaign_id, "Unknown", name, {}, {})
        entity_map[name] = created["entity_id"]
        return created["entity_id"]

    for relationship in extraction.relationships:
        from_id = resolve_entity_id(relationship.from_entity_name)
        to_id = resolve_entity_id(relationship.to_entity_name)
        created = create_relationship(
            campaign_id,
            from_id,
            to_id,
            relationship.type,
            relationship.properties,
        )
        if not created:
            raise HTTPException(status_code=404, detail="Entity not found")

    return extraction
