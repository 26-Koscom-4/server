from typing import Dict

from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema
from app.domain.user.schema.investment_test.dto import (
    InvestmentQuestion,
    InvestmentType,
    ResultChart,
    TestResult,
    TestState,
)


class InvestmentTestResponse(BaseSchema):
    investmentTypes: Dict[str, InvestmentType]
    investmentQuestions: list[InvestmentQuestion]
    testState: TestState
    testResult: TestResult
    resultChart: ResultChart

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "investmentTypes": {
                        "conservative": {
                            "name": "Conservative",
                            "icon": "C",
                            "description": "Prefer stability.",
                            "characteristics": ["Low risk", "Capital preservation"],
                            "portfolios": ["Dividend Village"],
                        }
                    },
                    "investmentQuestions": [
                        {
                            "id": "q1",
                            "question": "Which statement fits you best?",
                            "answers": [
                                {
                                    "id": "q1_a1",
                                    "text": "Preserve principal",
                                    "weights": {"conservative": 5},
                                }
                            ],
                        }
                    ],
                    "testState": {
                        "currentQuestionIndex": 0,
                        "userAnswers": [],
                        "progress": {"current": 1, "total": 25},
                    },
                    "testResult": {
                        "scores": {"conservative": 10},
                        "percentages": {"conservative": "20.0"},
                        "mainType": "conservative",
                    },
                    "resultChart": {
                        "type": "doughnut",
                        "data": {
                            "labels": ["Conservative"],
                            "datasets": [
                                {
                                    "data": [20.0],
                                    "backgroundColor": ["rgba(78,205,196,0.8)"],
                                    "borderWidth": 2,
                                    "borderColor": "#fff",
                                }
                            ],
                        },
                        "options": {"responsive": True, "cutout": "60%"},
                    },
                }
            ]
        },
    )
