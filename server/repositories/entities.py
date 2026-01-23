from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from server.db.neo4j import get_session
from server.repositories.utils import node_to_dict


def create_entity(
    campaign_id: str,
    entity_type: str,
    name: str,
    properties: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """创建实体节点（Neo4j只存基本信息，属性存SQLite）"""
    created_at = datetime.utcnow()

    # Check if entity already exists
    existing = get_entity_by_name(campaign_id, name)

    if existing:
        entity_id = existing["entity_id"]
        is_new = False
        should_update_type = existing.get("type") == "Unknown"
    else:
        entity_id = str(uuid4())
        is_new = True
        should_update_type = True

    # Build query - Neo4j只存基本信息，属性存SQLite
    query = (
        "MATCH (c:Campaign {campaign_id: $campaign_id}) "
        "MERGE (e:Entity { campaign_id: $campaign_id, name: $name }) "
        "SET "
        "e.entity_id = $entity_id, "
        "e.updated_at = $updated_at"
    )

    # Update type if it's a new entity or if upgrading from "Unknown"
    if should_update_type:
        query += ", e.type = $entity_type "

    if is_new:
        query += ", e.created_at = $created_at "

    query += " MERGE (e)-[:IN_CAMPAIGN]->(c) RETURN e"

    with get_session() as session:
        result = session.run(
            query,
            {
                "campaign_id": campaign_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "name": name,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
        record = result.single()
    return node_to_dict(record["e"], [])


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
