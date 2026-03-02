from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    groq_api_key: str
    amadeus_api_key: str = "" 
    amadeus_api_secret: str = ""   
    
    # Snowflake Configuration (all optional)
    snowflake_account: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_password: Optional[str] = None
    snowflake_database: str = "FINDER_AI"
    snowflake_schema: str = "PUBLIC"
    snowflake_warehouse: str = "COMPUTE_WH"
    
    # Application Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Memory Settings
    max_conversation_history: int = 10
    session_timeout_minutes: int = 30
    
    # Model Settings
    model_name: str = "llama-3.3-70b-versatile"
    model_temperature: float = 0.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()