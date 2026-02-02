"""개미 마을 수석 이장 브리핑 생성 오케스트레이션. 실시간 시세·뉴스 파이프라인 통합."""

import logging
from typing import Any, Dict, List, Optional

from app.domain.briefing.schema.dto import (
    AssetAnalysisItem,
    BriefingCard,
    BriefingCardHeader,
    StatusSection,
    StrategySection,
    VillageBriefing,
)
from app.domain.briefing.schema.request import BriefingGenerateRequest, NewsItem
from app.domain.briefing.schema.response import BriefingGenerateResponse
from app.services.briefing.llm import call_llm
from app.services.briefing.parser import parse_briefing_response
from app.services.briefing.prompt import (
    build_system_prompt,
    build_user_prompt,
    news_to_json,
    villages_to_json,
)
from app.services.market_data import MarketContext, get_market_context

logger = logging.getLogger(__name__)

# 마을 type/goal → 한국어 라벨 (이미지 UI용)
TYPE_TEXT_MAP: Dict[str, str] = {
    "growth": "성장형",
    "dividend": "배당형",
    "leverage": "레버리지형",
    "domestic": "국내주식",
    "etf": "글로벌 ETF",
    "semiconductor": "반도체 섹터",
}
GOAL_TEXT_MAP: Dict[str, str] = {
    "long-term": "장기 투자",
    "passive-income": "배당 수익",
    "high-risk": "고위험/고수익",
    "balanced": "균형 투자",
    "diversification": "분산 투자",
    "sector-focus": "섹터 집중",
}
ADVICE_MAP: Dict[str, str] = {
    "growth": "성장주는 장기적인 관점에서 접근하세요. 단기 변동성에 흔들리지 마세요.",
    "dividend": "배당주는 안정적인 현금 흐름을 제공하며 배당락일 체크가 필요합니다.",
    "leverage": "레버리지 상품은 변동성이 크니 리스크 관리가 중요합니다.",
    "domestic": "국내 시장의 지표 변화와 대외 변수를 함께 확인하세요.",
    "etf": "글로벌 분산 투자로 리스크를 줄이고 안정적인 수익을 추구하세요.",
    "semiconductor": "반도체 업황과 글로벌 수요 지표를 주의 깊게 살펴보세요.",
}
MARKET_ADVICE_MAP: Dict[str, str] = {
    "growth": "기술주 중심 포트폴리오입니다. 실적 발표 시즌을 주목하세요.",
    "dividend": "배당락일이 가까우니 배당 일정과 수익률을 확인하세요.",
    "leverage": "VIX 지수가 상승 중입니다. 변동성 관리가 필요합니다.",
    "domestic": "국내 증시 변동성이 커질 수 있습니다.",
    "etf": "글로벌 시장이 안정적으로 보이고 있습니다.",
    "semiconductor": "반도체 업황 지표를 체크하세요.",
}
DEFAULT_CHECKLIST: List[str] = [
    "시장 변동성 모니터링",
    "주요 뉴스 확인",
    "리밸런싱 필요 여부 검토",
]


def _extract_tickers(villages: List[Any]) -> List[str]:
    """villages 내 모든 asset의 ticker 수집 (중복 제거)."""
    seen: set = set()
    out: List[str] = []
    for v in villages:
        for a in getattr(v, "assets", []) or []:
            t = getattr(a, "ticker", None) or (a.get("ticker") if isinstance(a, dict) else None)
            if t and t not in seen:
                seen.add(t)
                out.append(t)
    return out


def _market_news_to_request_news_items(ctx: MarketContext) -> List[NewsItem]:
    """MarketContext.news_items를 BriefingGenerateRequest용 NewsItem 리스트로 변환."""
    return [
        NewsItem(
            title=item.get("title") or "",
            summary=item.get("summary"),
            source=item.get("source"),
            tickers=item.get("tickers"),
        )
        for item in ctx.news_items
    ]


def _build_briefing_card(
    village: Dict[str, Any],
    user_name: str = "주인님",
    time_slot: str = "morning",
    advice_override: Optional[List[str]] = None,
    checklist_override: Optional[List[str]] = None,
) -> BriefingCard:
    """한 마을 데이터로 개미 아침 브리핑 카드(이미지 UI) 구성."""
    slot = "아침" if time_slot == "morning" else "저녁"
    v_type = village.get("type") or "growth"
    v_goal = village.get("goal") or "long-term"
    intro = f"{user_name}, 좋은 {slot}입니다! {village.get('name', '')}의 현재 상황을 알려드립니다."

    advice = advice_override or []
    if not advice:
        a1 = ADVICE_MAP.get(v_type, ADVICE_MAP["growth"])
        a2 = MARKET_ADVICE_MAP.get(v_type, MARKET_ADVICE_MAP["growth"])
        advice = [a1, f"✓ {a2}"]

    checklist = checklist_override or [f"✓ {c}" for c in DEFAULT_CHECKLIST]

    return BriefingCard(
        header=BriefingCardHeader(
            title="개미 아침 브리핑",
            subtitle="마을별 대표 개미를 선택하고 브리핑을 들어보세요",
        ),
        village=VillageBriefing(
            id=village.get("id", ""),
            name=village.get("name", ""),
            icon=village.get("icon", ""),
            briefing_title=f"{village.get('name', '')} 브리핑",
        ),
        status=StatusSection(
            intro_sentence=intro,
            total_assets=village.get("totalValue") or 0,
            return_rate=village.get("returnRate") or 0.0,
            portfolio_weight=village.get("allocation") or 0.0,
        ),
        asset_analysis=[
            AssetAnalysisItem(
                ticker=a.get("ticker", a.get("id", "")),
                type=a.get("type", ""),
                status="안정적으로 운영 중입니다.",
            )
            for a in (village.get("assets") or [])
        ],
        strategy=StrategySection(
            investment_type=TYPE_TEXT_MAP.get(v_type, "성장형"),
            investment_goal=GOAL_TEXT_MAP.get(v_goal, "장기 투자"),
        ),
        advice=advice,
        checklist=checklist,
    )


async def generate_briefing(req: BriefingGenerateRequest) -> BriefingGenerateResponse:
    """
    포트폴리오(villages) 기준으로 실시간 시세·뉴스를 먼저 확보한 뒤 Voice Script + Visual Summary 생성.
    get_market_context 실패 시 빈 시세/뉴스로 진행; LLM 키 없으면 목(mock) 브리핑 반환.
    """
    villages_data = [v.model_dump(exclude_none=True) for v in req.villages]
    villages_json = villages_to_json(villages_data)
    tickers = _extract_tickers(req.villages)

    # 실시간 데이터 파이프라인: 시세·뉴스 수집 (실패 시 빈 MarketContext)
    market_ctx = await get_market_context(tickers, news_per_ticker=3)
    news_for_prompt: List[NewsItem] = _market_news_to_request_news_items(market_ctx)
    if req.news_items:
        news_for_prompt = list(req.news_items) + news_for_prompt

    news_json: Optional[str] = None
    if news_for_prompt:
        news_json = news_to_json([n.model_dump(exclude_none=True) for n in news_for_prompt])

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(
        villages_json=villages_json,
        news_json=news_json,
        market_quotes=market_ctx.ticker_quotes or None,
        user_name=req.user_name or "김직장님",
        time_slot=req.time_slot,
    )

    raw = call_llm(system_prompt, user_prompt)
    user_name = req.user_name or "주인님"
    first_village = villages_data[0] if villages_data else {}

    if raw:
        voice_script, visual_summary = parse_briefing_response(raw)
        advice = visual_summary.get("advice")
        checklist = visual_summary.get("checklist")
        if isinstance(advice, list):
            advice = [str(x) for x in advice]
        else:
            advice = None
        if isinstance(checklist, list):
            checklist = [str(x) for x in checklist]
        else:
            checklist = None
        card = _build_briefing_card(
            first_village,
            user_name=user_name,
            time_slot=req.time_slot,
            advice_override=advice,
            checklist_override=checklist,
        )
        return BriefingGenerateResponse(voice_script=voice_script, briefing_card=card)

    return _mock_briefing(req, villages_data, market_ctx)


def _mock_briefing(
    req: BriefingGenerateRequest,
    villages_data: List[Dict[str, Any]],
    market_ctx: Optional[MarketContext] = None,
) -> BriefingGenerateResponse:
    """API 키 없을 때 또는 LLM 실패 시 사용하는 목 브리핑. 실시간 시세가 있으면 voice_script에 반영."""
    name = req.user_name or "주인님"
    slot = "아침" if req.time_slot == "morning" else "저녁"
    total_value = sum(v.get("totalValue") or 0 for v in villages_data)
    rates = [v.get("returnRate") for v in villages_data if v.get("returnRate") is not None]
    avg_rate = sum(r for r in rates if r is not None) / len(rates) if rates else 0.0

    quote_mentions: List[str] = []
    if market_ctx and market_ctx.ticker_quotes:
        for q in market_ctx.ticker_quotes[:3]:
            if q.price is not None and q.change_percent is not None:
                direction = "상승" if q.change_percent >= 0 else "하락"
                quote_mentions.append(f"{q.ticker}는 {q.price:.0f}달러로 {abs(q.change_percent):.1f}% {direction} 중입니다.")
    extra = " ".join(quote_mentions) + " " if quote_mentions else ""

    voice_script = (
        f"좋은 {slot}입니다, {name}. "
        "오늘도 개미 마을 브리핑을 확인해 주세요. "
        f"전체 자산은 약 {total_value:,}원, 평균 수익률은 {avg_rate:.1f}% 수준입니다. "
        + extra
        + "미장마을·배당마을·레버리지마을 순으로 요약해 드릴게요. "
        "성장주 비중이 높다면 원자재 마을도 한번 구경해 보시길 추천합니다. "
        "본 내용은 투자 조언이 아니며, 투자 결정은 본인 판단과 책임입니다."
    )
    first_village = villages_data[0] if villages_data else {}
    card = _build_briefing_card(first_village, user_name=name, time_slot=req.time_slot)
    return BriefingGenerateResponse(voice_script=voice_script, briefing_card=card)
