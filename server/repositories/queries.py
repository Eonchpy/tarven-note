import logging
from typing import Any, Dict, List, Literal, Optional

from server.db.neo4j import get_session
from server.repositories.utils import deserialize_map
from server.repositories.sqlite_entities import get_entities_by_names

logger = logging.getLogger(__name__)


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
    entity_id: Optional[str] = None,
    name: Optional[str] = None,
    depth: int = 2,
    detail_level: Literal["skeleton", "summary", "full"] = "skeleton",
) -> Dict[str, List[Dict[str, Any]]]:
    logger.info(f"get_subgraph called: campaign_id={campaign_id}, entity_id={entity_id}, name={name}, depth={depth}")
    depth = max(1, min(depth, 4))

    # Build match clause based on provided parameter
    if entity_id:
        match_clause = "MATCH (center:Entity {entity_id: $entity_id})-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id})"
        params = {"campaign_id": campaign_id, "entity_id": entity_id}
    elif name:
        match_clause = "MATCH (center:Entity {name: $name})-[:IN_CAMPAIGN]->(:Campaign {campaign_id: $campaign_id})"
        params = {"campaign_id": campaign_id, "name": name}
    else:
        return {"nodes": [], "edges": []}

    query = (
        f"{match_clause} "
        "OPTIONAL MATCH path = (center)-[*1.." + str(depth) + "]-(n:Entity) "
        "WITH center, collect(path) AS paths "
        "WITH center, paths, "
        "CASE WHEN size(paths) = 0 THEN [center] "
        "ELSE reduce(acc = [], p IN paths | acc + nodes(p)) + [center] END AS allNodes, "
        "CASE WHEN size(paths) = 0 THEN [] "
        "ELSE reduce(acc = [], p IN paths | acc + relationships(p)) END AS allRels "
        "UNWIND allNodes AS n "
        "WITH center, allRels, collect(DISTINCT n) AS nodes "
        "RETURN nodes, allRels AS rels"
    )
    logger.info(f"Query: {query}")
    logger.info(f"Params: {params}")
    with get_session() as session:
        result = session.run(query, params)
        record = result.single()
        if not record:
            logger.info("No record returned from query")
            return {"nodes": [], "edges": []}

        logger.info(f"Raw record nodes count: {len(record['nodes'])}")
        logger.info(f"Raw record rels count: {len(record['rels'])}")

        nodes = [
            {
                "id": node.get("entity_id"),
                "entity_id": node.get("entity_id"),
                "label": node.get("name"),
                "type": node.get("type"),
                "properties": {},
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

        # 根据 detail_level 补充属性
        if detail_level != "skeleton" and nodes:
            node_names = [n["label"] for n in nodes]
            sqlite_data = get_entities_by_names(campaign_id, node_names)
            skip_keys = {"id", "entity_id", "campaign_id", "type", "name", "created_at", "updated_at"}

            for node in nodes:
                entity_data = sqlite_data.get(node["label"])
                if entity_data:
                    if detail_level == "summary":
                        # summary: 只返回 description
                        node["properties"] = {
                            "description": entity_data.get("description")
                        } if entity_data.get("description") else {}
                    elif detail_level == "full":
                        # full: 返回所有属性
                        node["properties"] = {
                            k: v for k, v in entity_data.items()
                            if k not in skip_keys and v is not None
                        }

        logger.info(f"Processed nodes count: {len(nodes)}, edges count: {len(edges)}")
        return {"nodes": nodes, "edges": edges}
