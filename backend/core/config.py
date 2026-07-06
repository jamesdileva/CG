"""Application configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    ollama_model: str = "qwen3:8b"
    ollama_timeout_seconds: int = 1200

    # TTS
    tts_provider: str = "edge-tts"  # "edge-tts"
    tts_voice: str = "en-US-JennyNeural"
    tts_timeout_seconds: int = 600

    # YouTube / OAuth
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_token_path: str = "data/youtube_token.json"

    # Research
    research_scrape_timeout_seconds: int = 30
    research_max_sources: int = 8
    research_fact_limit: int = 60
    research_content_max_chars: int = 25000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
