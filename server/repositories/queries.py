from typing import Any, Dict, List

from server.db.neo4j import get_session
from server.repositories.utils import deserialize_map


def find_paths(
    campaign_id: str,
    from_name: str,
    to_name: str,
    max_hops: int,
) -> List[Dict[str, Any]]:
    max_hops = max(1, min(max_hops, 6))
    query = (
        "MATCH path = (from:Entity {name: $from_name})-"
        f"[*1..{max_hops}]-(to:Entity {{name: $to_name}}) "
        "WHERE (from)-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id}) "
        "AND (to)-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id}) "
        "RETURN path, length(path) AS hops "
        "ORDER BY hops ASC "
        "LIMIT 5"
    )
    with get_session() as session:
        result = session.run(
            query,
            {
                "campaign_id": campaign_id,
                "from_name": from_name,
                "to_name": to_name,
            },
        )
        paths: List[Dict[str, Any]] = []
        for record in result:
            path = record["path"]
            nodes = [node.get("name") for node in path.nodes]
            relationships = [rel.get("type") for rel in path.relationships]
            paths.append(
                {
                    "nodes": nodes,
                    "relationships": relationships,
                    "hops": record["hops"],
                }
            )
        return paths


def get_subgraph(
    campaign_id: str,
    entity_id: str,
    depth: int,
) -> Dict[str, List[Dict[str, Any]]]:
    depth = max(1, min(depth, 4))
    query = (
        "MATCH (center:Entity {entity_id: $entity_id})-[:IN_CAMPAIGN]->"
        "(:Campaign {campaign_id: $campaign_id}) "
        "CALL {"
        "  WITH center "
        f"  MATCH path = (center)-[*1..{depth}]-(n:Entity) "
        "  RETURN path"
        "} "
        "WITH collect(path) AS paths "
        "UNWIND paths AS p "
        "UNWIND nodes(p) AS n "
        "UNWIND relationships(p) AS r "
        "RETURN collect(DISTINCT n) AS nodes, collect(DISTINCT r) AS rels"
    )
    with get_session() as session:
        result = session.run(
            query,
            {
                "campaign_id": campaign_id,
                "entity_id": entity_id,
            },
        )
        record = result.single()
        if not record:
            return {"nodes": [], "edges": []}

        nodes = [
            {
                "id": node.get("entity_id"),
                "label": node.get("name"),
                "type": node.get("type"),
                "properties": deserialize_map(node.get("properties")),
            }
            for node in record["nodes"]
            if node.get("entity_id")
        ]
        edges = [
            {
                "id": rel.get("relationship_id"),
                "from_id": rel.start_node.get("entity_id"),
                "to_id": rel.end_node.get("entity_id"),
                "type": rel.get("type"),
                "properties": deserialize_map(rel.get("properties")),
            }
            for rel in record["rels"]
            if rel.get("relationship_id")
        ]
        return {"nodes": nodes, "edges": edges}
