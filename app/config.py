from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = "http://127.0.0.1:8080/v1"
    llm_api_key: str = "local"
    llm_model: str = "gemma-4-e2b-it"
    use_cpu: bool = True
    request_timeout_seconds: float = 180
    default_temperature: float = 1.0
    default_top_p: float = 0.95
    default_top_k: int = 64
    default_max_tokens: int = 512
    max_queue_size: int = 50


settings = Settings()
