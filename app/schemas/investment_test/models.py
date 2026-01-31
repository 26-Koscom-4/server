from typing import Any, Dict, List

from app.schemas.common.base import BaseSchema


class InvestmentType(BaseSchema):
    name: str
    icon: str
    description: str
    characteristics: List[str]
    portfolios: List[str]


class InvestmentAnswer(BaseSchema):
    id: str
    text: str
    weights: Dict[str, int]


class InvestmentQuestion(BaseSchema):
    id: str
    question: str
    answers: List[InvestmentAnswer]


class TestProgress(BaseSchema):
    current: int
    total: int


class TestState(BaseSchema):
    currentQuestionIndex: int
    userAnswers: List[int]
    progress: TestProgress


class TestResult(BaseSchema):
    scores: Dict[str, int]
    percentages: Dict[str, str]
    mainType: str


class ResultDataset(BaseSchema):
    data: List[float]
    backgroundColor: List[str]
    borderWidth: int
    borderColor: str


class ResultChartData(BaseSchema):
    labels: List[str]
    datasets: List[ResultDataset]


class ResultChart(BaseSchema):
    type: str
    data: ResultChartData
    options: Dict[str, Any]
