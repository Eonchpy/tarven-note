from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api.campaigns import router as campaigns_router
from server.api.entities import router as entities_router
from server.api.extract import router as extract_router
from server.api.health import router as health_router
from server.api.ingest import router as ingest_router
from server.api.queries import router as queries_router
from server.api.relationships import router as relationships_router
from server.db.neo4j import close_driver
from server.db.schema import apply_schema

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(campaigns_router)
app.include_router(entities_router)
app.include_router(relationships_router)
app.include_router(queries_router)
app.include_router(ingest_router)
app.include_router(extract_router)


@app.on_event("startup")
def startup_event():
    apply_schema()


@app.on_event("shutdown")
def shutdown_event():
    close_driver()
