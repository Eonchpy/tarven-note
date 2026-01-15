from fastapi import APIRouter, HTTPException

from server.repositories.entities import create_entity, get_entity_by_name
from server.repositories.relationships import create_relationship
from server.schemas.ingest import IngestRequest, IngestResponse
from server.services.normalizer import normalize_entity_type, normalize_relationship_type

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_handler(campaign_id: str, payload: IngestRequest):
    entity_map: dict[str, str] = {}

    for entity in payload.entities:
        normalized_type = normalize_entity_type(entity.type)
        created = create_entity(
            campaign_id,
            normalized_type,
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

    for relationship in payload.relationships:
        from_id = resolve_entity_id(relationship.from_entity_name)
        to_id = resolve_entity_id(relationship.to_entity_name)
        normalized_rel_type = normalize_relationship_type(relationship.type)
        created = create_relationship(
            campaign_id,
            from_id,
            to_id,
            normalized_rel_type,
            relationship.properties,
        )
        if not created:
            raise HTTPException(status_code=404, detail="Entity not found")

    return {
        "entities_count": len(payload.entities),
        "relationships_count": len(payload.relationships),
    }
