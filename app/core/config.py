from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "local"
    PROJECT_NAME: str = "KAMI"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/kami?charset=utf8mb4"

    DB_ENABLED: bool = True

    # AI 브리핑 (개미 마을 수석 이장)
    BRIEFING_LLM_PROVIDER: Literal["openai", "anthropic", "none"] = "none"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"

    # 스케줄 브리핑 (APScheduler: 9시·17시)
    BRIEFING_SCHEDULE_TIMEZONE: str = "Asia/Seoul"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
