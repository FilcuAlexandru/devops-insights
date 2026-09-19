import uuid

import pytest
from sqlalchemy import func, select

from devops_insights.ai.analysis import MAX_ATTEMPTS, analyze_repository
from devops_insights.ai.errors import AIServiceError, InvalidAIResponseError
from devops_insights.ai.persistence import get_repository_analyses, save_ai_analysis
from devops_insights.models import AIAnalysis
from tests.factories import make_repository, make_technology

VALID_RESPONSE = """## Summary
The repository is popular.

## Trends
There is insufficient historical data to identify a meaningful trend.

## Risks
The available data is insufficient for a risk assessment.

## Recommendations
The available data does not provide sufficient evidence for a specific recommendation.
"""


@pytest.fixture
def repository(session):
    return make_repository(session, make_technology(session), "k/main")


def script_responses(monkeypatch, responses: list):
    """Make the model return (or raise) the given items in order."""

    calls: list[str] = []
    queue = iter(responses)

    def fake_generate(prompt: str) -> str:
        calls.append(prompt)
        item = next(queue)

        if isinstance(item, Exception):
            raise item

        return item

    monkeypatch.setattr("devops_insights.ai.analysis.generate_response", fake_generate)

    return calls


def test_unknown_repository_returns_none(session) -> None:
    assert analyze_repository(session, uuid.uuid4()) is None


def test_analysis_is_generated_and_persisted(session, repository, monkeypatch) -> None:
    calls = script_responses(monkeypatch, [VALID_RESPONSE])

    analysis = analyze_repository(session, repository.id)

    assert analysis.response == VALID_RESPONSE.strip()
    assert analysis.repository_id == repository.id
    assert analysis.context["repository"]["full_name"] == "k/main"
    assert "k/main" in analysis.prompt
    assert len(calls) == 1


def test_invalid_output_is_retried_once(session, repository, monkeypatch) -> None:
    calls = script_responses(monkeypatch, ["no sections at all", VALID_RESPONSE])

    analysis = analyze_repository(session, repository.id)

    assert analysis.response == VALID_RESPONSE.strip()
    assert len(calls) == 2


def test_persistent_invalid_output_raises_and_stores_nothing(
    session, repository, monkeypatch
) -> None:
    calls = script_responses(monkeypatch, ["bad"] * MAX_ATTEMPTS)

    with pytest.raises(InvalidAIResponseError):
        analyze_repository(session, repository.id)

    assert len(calls) == MAX_ATTEMPTS
    assert session.scalar(select(func.count(AIAnalysis.id))) == 0


def test_service_errors_are_not_retried(session, repository, monkeypatch) -> None:
    calls = script_responses(monkeypatch, [AIServiceError("down")])

    with pytest.raises(AIServiceError):
        analyze_repository(session, repository.id)

    assert len(calls) == 1


def test_previous_analyses_are_kept(session, repository, monkeypatch) -> None:
    script_responses(monkeypatch, [VALID_RESPONSE, VALID_RESPONSE])

    first = analyze_repository(session, repository.id)
    second = analyze_repository(session, repository.id)

    assert {a.id for a in get_repository_analyses(session, repository.id)} == {first.id, second.id}


def test_save_ai_analysis_records_the_configured_model(session, repository) -> None:
    analysis = save_ai_analysis(session, repository.id, {"k": "v"}, "prompt", "response")

    assert analysis.model == "qwen3:1.7b"
    assert analysis.context == {"k": "v"}
    assert analysis.created_at is not None
