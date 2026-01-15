from server.db.neo4j import get_session


CONSTRAINT_NAMES = [
    "campaign_id_unique",
    "entity_id_unique",
    "relationship_id_unique",
]

INDEX_NAMES = [
    "campaign_name_index",
    "entity_name_index",
    "entity_campaign_index",
    "entity_type_index",
    "relationship_type_index",
]

CONSTRAINTS = [
    "CREATE CONSTRAINT campaign_id_unique IF NOT EXISTS FOR (c:Campaign) REQUIRE c.campaign_id IS UNIQUE",
    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
    "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR ()-[r]-() REQUIRE r.relationship_id IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX campaign_name_index IF NOT EXISTS FOR (c:Campaign) ON (c.name)",
    "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
    "CREATE INDEX entity_campaign_index IF NOT EXISTS FOR (e:Entity) ON (e.campaign_id)",
    "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
    "CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r]-() ON (r.type)",
]


def apply_schema() -> None:
    with get_session() as session:
        for statement in CONSTRAINTS:
            session.run(statement)
        for statement in INDEXES:
            session.run(statement)


def get_schema_status() -> dict:
    with get_session() as session:
        constraint_rows = session.run("SHOW CONSTRAINTS YIELD name RETURN name")
        index_rows = session.run("SHOW INDEXES YIELD name RETURN name")
        existing_constraints = {row["name"] for row in constraint_rows}
        existing_indexes = {row["name"] for row in index_rows}

    constraint_missing = sorted(set(CONSTRAINT_NAMES) - existing_constraints)
    index_missing = sorted(set(INDEX_NAMES) - existing_indexes)

    return {
        "constraints": {
            "expected": CONSTRAINT_NAMES,
            "present": sorted(set(CONSTRAINT_NAMES) & existing_constraints),
            "missing": constraint_missing,
        },
        "indexes": {
            "expected": INDEX_NAMES,
            "present": sorted(set(INDEX_NAMES) & existing_indexes),
            "missing": index_missing,
        },
        "ok": not constraint_missing and not index_missing,
    }
