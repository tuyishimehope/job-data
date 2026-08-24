from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    app_name: str = "Job Data Ingestion Platform Backend"
    greenhouse_url: str = ""
    llm_api_url : str = ""
    nvidia_api_key : str = ""
    hf_token: str = ""
    hf_url: str = ""
    OPENAI_API_KEY: str = ""
    

settings = Settings()