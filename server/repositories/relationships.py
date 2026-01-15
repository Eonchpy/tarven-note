from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from server.db.neo4j import get_session
from server.repositories.utils import relationship_to_dict, serialize_map


def create_relationship(
    campaign_id: str,
    from_entity_id: str,
    to_entity_id: str,
    relationship_type: str,
    properties: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    relationship_id = str(uuid4())
    rel_type = relationship_type  # Already normalized by ingest API
    created_at = datetime.utcnow()
    properties_payload = serialize_map(properties)
    query = (
        "MATCH (from:Entity {entity_id: $from_entity_id})-[:IN_CAMPAIGN]->"
        "(:Campaign {campaign_id: $campaign_id}) "
        "MATCH (to:Entity {entity_id: $to_entity_id})-[:IN_CAMPAIGN]->"
        "(:Campaign {campaign_id: $campaign_id}) "
        f"CREATE (from)-[r:{rel_type} {{ "
        "relationship_id: $relationship_id, "
        "type: $relationship_type, "
        "properties: $properties, "
        "created_at: $created_at, "
        "updated_at: $created_at "
        "}]->(to) "
        "RETURN r"
    )
    with get_session() as session:
        result = session.run(
            query,
            {
                "campaign_id": campaign_id,
                "from_entity_id": from_entity_id,
                "to_entity_id": to_entity_id,
                "relationship_id": relationship_id,
                "relationship_type": relationship_type,
                "properties": properties_payload,
                "created_at": created_at,
            },
        )
        record = result.single()
    return relationship_to_dict(record["r"], ["properties"]) if record else None


def list_relationships(
    campaign_id: str,
    from_entity_id: Optional[str] = None,
    to_entity_id: Optional[str] = None,
    relationship_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filters = [
        "(from:Entity)-[r]->(to:Entity)",
        "(from)-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id})",
        "(to)-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id})",
    ]
    params: Dict[str, Any] = {"campaign_id": campaign_id}
    if from_entity_id:
        filters.append("from.entity_id = $from_entity_id")
        params["from_entity_id"] = from_entity_id
    if to_entity_id:
        filters.append("to.entity_id = $to_entity_id")
        params["to_entity_id"] = to_entity_id
    if relationship_type:
        filters.append("r.type = $relationship_type")
        params["relationship_type"] = relationship_type

    where_clause = " AND ".join(filters[1:])
    query = (
        "MATCH (from:Entity)-[r]->(to:Entity) "
        f"WHERE {where_clause} "
        "RETURN r, from.entity_id AS from_entity_id, to.entity_id AS to_entity_id"
    )
    with get_session() as session:
        result = session.run(query, params)
        return [
            {
                **relationship_to_dict(record["r"], ["properties"]),
                "from_entity_id": record["from_entity_id"],
                "to_entity_id": record["to_entity_id"],
            }
            for record in result
        ]


def delete_relationship(campaign_id: str, relationship_id: str) -> bool:
    query = (
        "MATCH (c:Campaign {campaign_id: $campaign_id})<-[:IN_CAMPAIGN]-"
        "(from:Entity)-[r {relationship_id: $relationship_id}]->"
        "(to:Entity)-[:IN_CAMPAIGN]->(c) "
        "DELETE r "
        "RETURN COUNT(r) AS deleted"
    )
    with get_session() as session:
        result = session.run(
            query,
            {"campaign_id": campaign_id, "relationship_id": relationship_id},
        )
        record = result.single()
    return record["deleted"] > 0
