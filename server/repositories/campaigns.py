from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from server.db.neo4j import get_session


def create_campaign(name: str, system: str, description: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
    campaign_id = str(uuid4())
    created_at = datetime.utcnow()
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
                "metadata": metadata,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
        record = result.single()
    return record["c"]


def list_campaigns() -> List[Dict[str, Any]]:
    with get_session() as session:
        result = session.run(
            """
            MATCH (c:Campaign)
            RETURN c
            ORDER BY c.created_at DESC
            """
        )
        return [record["c"] for record in result]


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
    return record["c"] if record else None


def update_campaign(
    campaign_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    updates["updated_at"] = datetime.utcnow()
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
    return record["c"] if record else None


def delete_campaign(campaign_id: str) -> bool:
    with get_session() as session:
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
