from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
