"""
스케줄용 브리핑: yfinance 뉴스 수집 → OpenAI(gpt-4o-mini)로 '오늘의 투자 포인트' 한국어 요약 → 저장.
APScheduler에서 9시/17시에 호출.
"""

import logging
from datetime import datetime
from typing import List, Optional

from app.core.briefing_store import set_latest
from app.core.config import settings
from app.utils.fixtures import FixtureInvalid, FixtureNotFound, load_fixture

logger = logging.getLogger(__name__)

# OpenAI로 뉴스 제목 → '오늘의 투자 포인트' 한국어 요약
SYSTEM_PROMPT_KO = """당신은 투자 포트폴리오 맞춤형 뉴스 브리핑 전문가입니다.
주어진 뉴스 제목들을 바탕으로 '오늘의 투자 포인트'를 3~5문장으로 요약해 주세요.
반드시 한국어로만 작성하고, 핵심만 간결하게 전달하세요. 이모지나 기호는 사용하지 마세요."""


def _get_tickers_from_fixture() -> List[str]:
    """fixture villages에서 모든 ticker 수집."""
    try:
        data = load_fixture("ui_state_villages.json")
        villages = data.get("villages") or []
        seen = set()
        out = []
        for v in villages:
            for a in v.get("assets") or []:
                t = (a.get("ticker") or "").strip()
                if t and t not in seen:
                    seen.add(t)
                    out.append(t)
        return out
    except (FixtureNotFound, FixtureInvalid) as e:
        logger.warning("Failed to load villages fixture for tickers: %s", e)
        return []


def _summarize_news_with_openai(news_titles: List[str]) -> Optional[str]:
    """뉴스 제목 리스트를 OpenAI gpt-4o-mini로 한국어 요약. 실패 시 None."""
    if not news_titles:
        return None
    if not getattr(settings, "OPENAI_API_KEY", None) or not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set; skipping AI summary.")
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        user_content = "다음 뉴스 제목들을 '오늘의 투자 포인트'로 요약해 주세요.\n\n" + "\n".join(
            f"- {t}" for t in news_titles[:50]
        )
        resp = client.chat.completions.create(
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_KO},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        if resp.choices and resp.choices[0].message.content:
            return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.exception("OpenAI summary failed: %s", e)
    return None


def _run_scheduled_briefing_sync() -> None:
    """동기: 뉴스 수집 → OpenAI 요약 → 저장. 스케줄러 스레드에서 호출."""
    from app.services.market_data import _get_market_context_sync

    tickers = _get_tickers_from_fixture()
    if not tickers:
        logger.warning("No tickers; skipping scheduled briefing.")
        return

    ctx = _get_market_context_sync(tickers, news_per_ticker=5)
    news_titles = [item.get("title") or item.get("summary") or "" for item in ctx.news_items if item.get("title") or item.get("summary")]
    if not news_titles:
        summary = "오늘 수집된 보유 종목 관련 뉴스가 없습니다. 시장 상황을 직접 확인해 보시기 바랍니다."
        set_latest(summary=summary, news_count=0, tickers=tickers, generated_at=datetime.utcnow())
        logger.info("Scheduled briefing saved (no news).")
        return

    summary = _summarize_news_with_openai(news_titles)
    if not summary:
        summary = "오늘의 뉴스 요약 생성에 실패했습니다. 잠시 후 다시 시도해 주세요."
    set_latest(summary=summary, news_count=len(news_titles), tickers=tickers, generated_at=datetime.utcnow())
    logger.info("Scheduled briefing saved. news_count=%d", len(news_titles))


def run_scheduled_briefing() -> None:
    """
    스케줄 job 엔트리: 뉴스 수집 및 AI 요약 후 저장.
    APScheduler에서 9시/17시에 호출. 블로킹이므로 스레드에서 실행됨.
    """
    try:
        _run_scheduled_briefing_sync()
    except Exception as e:
        logger.exception("Scheduled briefing failed: %s", e)
