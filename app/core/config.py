from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = "local"
    PROJECT_NAME: str = "KAMI"
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
