import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def call_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call configured LLM provider and return raw text, or None when disabled/unavailable."""
    provider = settings.BRIEFING_LLM_PROVIDER

    if provider == "none":
        return None

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set; skipping LLM call.")
            return None
        try:
            from openai import OpenAI
        except Exception:  # pragma: no cover - import guard
            logger.exception("OpenAI package not available.")
            return None

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        if not resp.choices:
            return None
        return getattr(resp.choices[0].message, "content", None)

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY is not set; skipping LLM call.")
            return None
        try:
            import anthropic
        except Exception:  # pragma: no cover - import guard
            logger.exception("Anthropic package not available.")
            return None

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1200,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        chunks = []
        for block in getattr(resp, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                chunks.append(text)
        return "".join(chunks) if chunks else None

    logger.warning("Unknown BRIEFING_LLM_PROVIDER: %s", provider)
    return None
