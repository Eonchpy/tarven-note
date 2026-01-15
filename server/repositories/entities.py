from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from server.db.neo4j import get_session
from server.repositories.utils import normalize_label, node_to_dict, serialize_map


def create_entity(
    campaign_id: str,
    entity_type: str,
    name: str,
    properties: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    entity_id = str(uuid4())
    label = normalize_label(entity_type, prefix="E", upper=False)
    created_at = datetime.utcnow()
    properties_payload = serialize_map(properties)
    metadata_payload = serialize_map(metadata)
    query = (
        "MATCH (c:Campaign {campaign_id: $campaign_id}) "
        f"MERGE (e:Entity:{label} {{ campaign_id: $campaign_id, name: $name, type: $entity_type }}) "
        "ON CREATE SET "
        "e.entity_id = $entity_id, "
        "e.properties = $properties, "
        "e.metadata = $metadata, "
        "e.created_at = $created_at, "
        "e.updated_at = $created_at "
        "ON MATCH SET e.updated_at = $created_at "
        "MERGE (e)-[:IN_CAMPAIGN]->(c) "
        "RETURN e"
    )
    with get_session() as session:
        result = session.run(
            query,
            {
                "campaign_id": campaign_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "name": name,
                "properties": properties_payload,
                "metadata": metadata_payload,
                "created_at": created_at,
            },
        )
        record = result.single()
    return node_to_dict(record["e"], ["properties", "metadata"])


def list_entities(
    campaign_id: str,
    entity_type: Optional[str] = None,
    name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filters = []
    params: Dict[str, Any] = {"campaign_id": campaign_id}
    if entity_type:
        filters.append("e.type = $entity_type")
        params["entity_type"] = entity_type
    if name:
        filters.append("e.name = $name")
        params["name"] = name

    where_clause = " AND ".join(filters)
    query = (
        "MATCH (e:Entity)-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id}) "
        f"{('WHERE ' + where_clause) if where_clause else ''} "
        "RETURN e"
    )
    with get_session() as session:
        result = session.run(query, params)
        return [node_to_dict(record["e"], ["properties", "metadata"]) for record in result]


def get_entity(campaign_id: str, entity_id: str) -> Optional[Dict[str, Any]]:
    query = (
        "MATCH (e:Entity {entity_id: $entity_id})-[:IN_CAMPAIGN]->"
        "(:Campaign {campaign_id: $campaign_id}) "
        "RETURN e"
    )
    with get_session() as session:
        result = session.run(query, {"campaign_id": campaign_id, "entity_id": entity_id})
        record = result.single()
    return node_to_dict(record["e"], ["properties", "metadata"]) if record else None

def get_entity_by_name(
    campaign_id: str,
    name: str,
    entity_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    filters = ["e.name = $name"]
    params: Dict[str, Any] = {"campaign_id": campaign_id, "name": name}
    if entity_type:
        filters.append("e.type = $entity_type")
        params["entity_type"] = entity_type

    where_clause = " AND ".join(filters)
    query = (
        "MATCH (e:Entity)-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id}) "
        f"WHERE {where_clause} "
        "RETURN e LIMIT 1"
    )
    with get_session() as session:
        result = session.run(query, params)
        record = result.single()
    return node_to_dict(record["e"], ["properties", "metadata"]) if record else None

def update_entity(
    campaign_id: str,
    entity_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    updates["updated_at"] = datetime.utcnow()
    if "properties" in updates:
        updates["properties"] = serialize_map(updates["properties"])
    if "metadata" in updates:
        updates["metadata"] = serialize_map(updates["metadata"])
    query = (
        "MATCH (e:Entity {entity_id: $entity_id})-[:IN_CAMPAIGN]->"
        "(:Campaign {campaign_id: $campaign_id}) "
        "SET e += $updates "
        "RETURN e"
    )
    with get_session() as session:
        result = session.run(
            query,
            {
                "campaign_id": campaign_id,
                "entity_id": entity_id,
                "updates": updates,
            },
        )
        record = result.single()
    return node_to_dict(record["e"], ["properties", "metadata"]) if record else None

def delete_entity(campaign_id: str, entity_id: str) -> bool:
    query = (
        "MATCH (e:Entity {entity_id: $entity_id})-[:IN_CAMPAIGN]->"
        "(:Campaign {campaign_id: $campaign_id}) "
        "DETACH DELETE e "
        "RETURN COUNT(e) AS deleted"
    )
    with get_session() as session:
        result = session.run(query, {"campaign_id": campaign_id, "entity_id": entity_id})
        record = result.single()
    return record["deleted"] > 0
