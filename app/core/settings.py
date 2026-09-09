from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Job Data Ingestion Platform Backend"
    greenhouse_url: str = ""
    llm_api_url: str = ""
    nvidia_api_key: str = ""
    hf_token: str = ""
    hf_url: str = ""
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    environment: str = ""
    NEW_RELIC_LICENSE_KEY: str = ""
    new_relic_user_key: str = ""
    new_relic_log_url: str = ""
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_OTLP_PROTOCOL: str = ""
    OTEL_EXPORTER_OTLP_HEADERS: str = ""


settings = Settings()
