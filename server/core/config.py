from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    # SQLite settings
    sqlite_db_path: str = "data/tarven_note.db"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    class Config:
        env_file = ".env"


settings = Settings()
