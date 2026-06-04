"""Application configuration"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # FastAPI
    app_name: str = "AI Documentary Studio"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # LLM
    llm_provider: str = "mock"  # "mock" or "ollama" or "openai"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    class Config:
        env_file = ".env"


settings = Settings()
