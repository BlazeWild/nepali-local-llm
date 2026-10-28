from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llama_base_url: str = "http://127.0.0.1:8080/v1"
    llama_api_key: str = "local"
    llm_api_key: str
    llm_model: str = "google/gemma-4-12B-it-qat-q4_0-gguf:Q4_0"
    use_cpu: bool = False
    request_timeout_seconds: float = 180
    default_temperature: float = 1.0
    default_top_p: float = 0.95
    default_top_k: int = 64
    default_max_tokens: int = 4096
    max_queue_size: int = 50


settings = Settings()
