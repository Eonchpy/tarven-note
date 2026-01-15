from neo4j import GraphDatabase

from server.core.config import settings


driver = GraphDatabase.driver(
    settings.neo4j_uri,
    auth=(settings.neo4j_user, settings.neo4j_password),
)


def get_session():
    return driver.session()


def close_driver():
    driver.close()


def ping() -> dict:
    try:
        with get_session() as session:
            result = session.run("RETURN 1 AS ok")
            record = result.single()
        return {"ok": bool(record and record["ok"] == 1)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
