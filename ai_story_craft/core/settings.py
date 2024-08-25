from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    whisper_model: str = 'medium'
    assistant_model: str = 'gpt-4o'
    openai_api_key: str

    telegram_bot_token: str
    new_session_timeout: int = 3600

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    LANGFUSE_HOST: str = 'http://localhost:3000'
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str

    model_config = ConfigDict(extra='ignore')


settings = Settings(_env_file='../.env')
