from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    whisper_model: str = 'medium'


settings = Settings(_env_file='.env')
