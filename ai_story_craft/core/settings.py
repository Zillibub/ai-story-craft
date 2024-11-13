from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    whisper_model: str = 'turbo'
    assistant_model: str = 'gpt-4o'
    OPENAI_API_KEY: str

    telegram_bot_token: str
    new_session_timeout: int = 3600

    working_directory: str
    videos_directory: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    CELERY_BROKER_URL: str = 'pyamqp://'
    CELERY_BACKEND_URL: str = 'redis://localhost'

    # LANGFUSE_HOST: str = 'http://localhost:3000'
    # LANGFUSE_PUBLIC_KEY: str
    # LANGFUSE_SECRET_KEY: str

    model_config = ConfigDict(extra='ignore')


settings = Settings(_env_file='../.env')
