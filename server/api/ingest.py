from fastapi import APIRouter, HTTPException

from server.repositories.campaigns import ensure_campaign_exists
from server.repositories.entities import create_entity, get_entity_by_name
from server.repositories.relationships import create_relationship
from server.repositories.sqlite_entities import upsert_entity as sqlite_upsert
from server.schemas.ingest import IngestRequest, IngestResponse
from server.services.normalizer import normalize_entity_type

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_handler(campaign_id: str, payload: IngestRequest):
    # 自动创建 campaign（如果不存在）
    ensure_campaign_exists(campaign_id)

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

        # 同时写入 SQLite（存储详细属性）
        sqlite_upsert(
            entity_id=created["entity_id"],
            campaign_id=campaign_id,
            entity_type=normalized_type,
            name=entity.name,
            properties=entity.properties,
            metadata=entity.metadata,
        )

    def resolve_entity_id(name: str) -> str:
        if name in entity_map:
            return entity_map[name]
        existing = get_entity_by_name(campaign_id, name)
        if existing:
            entity_map[name] = existing["entity_id"]
            return existing["entity_id"]
        created = create_entity(campaign_id, "Unknown", name, {}, {})
        entity_map[name] = created["entity_id"]
        # 同时写入 SQLite
        sqlite_upsert(
            entity_id=created["entity_id"],
            campaign_id=campaign_id,
            entity_type="Unknown",
            name=name,
            properties={},
        )
        return created["entity_id"]

    rel_count = 0
    for relationship in payload.relationships:
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
        rel_count += 1

        # 如果是双向关系，创建反向关系
        if relationship.bidirectional:
            # 使用 reverse_type，如果没有指定则使用相同的 type
            rev_type = relationship.reverse_type or relationship.type
            reverse = create_relationship(
                campaign_id,
                to_id,
                from_id,
                rev_type,
                relationship.properties,
            )
            if reverse:
                rel_count += 1

    return {
        "entities_count": len(payload.entities),
        "relationships_count": rel_count,
    }
