from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from server.db.neo4j import get_session
from server.repositories.utils import node_to_dict, serialize_map


def create_campaign(name: str, system: str, description: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
    campaign_id = str(uuid4())
    created_at = datetime.utcnow()
    metadata_payload = serialize_map(metadata)
    with get_session() as session:
        result = session.run(
            """
            CREATE (c:Campaign {
              campaign_id: $campaign_id,
              name: $name,
              system: $system,
              description: $description,
              status: $status,
              metadata: $metadata,
              created_at: $created_at,
              updated_at: $updated_at
            })
            RETURN c
            """,
            {
                "campaign_id": campaign_id,
                "name": name,
                "system": system,
                "description": description,
                "status": "active",
                "metadata": metadata_payload,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
        record = result.single()
    return node_to_dict(record["c"], ["metadata"]) if record else None


def list_campaigns() -> List[Dict[str, Any]]:
    with get_session() as session:
        result = session.run(
            """
            MATCH (c:Campaign)
            RETURN c
            ORDER BY c.created_at DESC
            """
        )
        return [node_to_dict(record["c"], ["metadata"]) for record in result]


def get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        result = session.run(
            """
            MATCH (c:Campaign {campaign_id: $campaign_id})
            RETURN c
            """,
            {"campaign_id": campaign_id},
        )
        record = result.single()
    return node_to_dict(record["c"], ["metadata"]) if record else None


def update_campaign(
    campaign_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    updates["updated_at"] = datetime.utcnow()
    if "metadata" in updates:
        updates["metadata"] = serialize_map(updates["metadata"])
    with get_session() as session:
        result = session.run(
            """
            MATCH (c:Campaign {campaign_id: $campaign_id})
            SET c += $updates
            RETURN c
            """,
            {"campaign_id": campaign_id, "updates": updates},
        )
        record = result.single()
    return node_to_dict(record["c"], ["metadata"]) if record else None


def delete_campaign(campaign_id: str) -> bool:
    with get_session() as session:
        # 先删除所有关联的实体及其关系
        session.run(
            """
            MATCH (e:Entity)-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id})
            DETACH DELETE e
            """,
            {"campaign_id": campaign_id},
        )
        # 再删除战役节点
        result = session.run(
            """
            MATCH (c:Campaign {campaign_id: $campaign_id})
            DETACH DELETE c
            RETURN COUNT(c) AS deleted
            """,
            {"campaign_id": campaign_id},
        )
        record = result.single()
    return record["deleted"] > 0
