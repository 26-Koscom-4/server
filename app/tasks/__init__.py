"""백그라운드 작업 엔트리 포인트. Celery/cron에서 호출 가능."""

from app.tasks.briefing_task import run_morning_briefing

__all__ = ["run_morning_briefing"]
