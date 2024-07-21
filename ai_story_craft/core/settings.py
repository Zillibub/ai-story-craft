from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    whisper_model: str = 'medium'
    assistant_model: str = 'gpt-4o'
    openai_api_key: str
    database_url: str


settings = Settings(_env_file='../.env')
