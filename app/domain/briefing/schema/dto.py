from typing import List, Optional

from app.domain.common.schema.dto import BaseSchema


# --- 개미 아침 브리핑 카드 UI (이미지 구조) ---


class BriefingCardHeader(BaseSchema):
    """헤더: 제목, 부제목."""

    title: str = "개미 아침 브리핑"
    subtitle: str = "마을별 대표 개미를 선택하고 브리핑을 들어보세요"


class VillageBriefing(BaseSchema):
    """카드 상단: 마을 식별자."""

    id: str
    name: str
    icon: str
    briefing_title: str  # e.g. "미장마을 브리핑"


class StatusSection(BaseSchema):
    """미장마을 현황: 인사 문장, 총 자산, 수익률, 포트폴리오 비중."""

    intro_sentence: str
    total_assets: int
    return_rate: float
    portfolio_weight: float


class AssetAnalysisItem(BaseSchema):
    """보유 자산 분석 한 건: 티커, 유형, 상태 문장."""

    ticker: str
    type: str
    status: str = "안정적으로 운영 중입니다."


class StrategySection(BaseSchema):
    """투자 전략: 유형, 목표 (한국어 라벨)."""

    investment_type: str
    investment_goal: str


class BriefingCard(BaseSchema):
    """브리핑 카드 전체 구조 (이미지 UI)."""

    header: BriefingCardHeader
    village: VillageBriefing
    status: StatusSection
    asset_analysis: List[AssetAnalysisItem]
    strategy: StrategySection
    advice: List[str]
    checklist: List[str]


# --- 기존 selector/selected village ---


class SelectorVillage(BaseSchema):
    id: str
    name: str
    icon: str
    returnRate: float


class Selector(BaseSchema):
    villages: List[SelectorVillage]


class BriefingAsset(BaseSchema):
    id: str
    name: str
    type: str
    ticker: str
    value: Optional[int] = None


class SelectedVillage(BaseSchema):
    id: str
    name: str
    icon: str
    totalValue: int
    returnRate: float
    allocation: float
    assets: List[BriefingAsset]

