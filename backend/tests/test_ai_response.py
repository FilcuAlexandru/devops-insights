import pytest

from devops_insights.ai.errors import InvalidAIResponseError
from devops_insights.ai.response import extract_section, validate_ai_response

VALID_RESPONSE = """## Summary

The repository shows active project activity.

## Trends

There is insufficient historical data to identify a reliable trend.

## Risks

The available data does not support identifying specific risks.

## Recommendations

Continue monitoring project activity.
"""


def test_valid_response_is_accepted() -> None:
    assert validate_ai_response(VALID_RESPONSE) == VALID_RESPONSE.strip()


def test_surrounding_whitespace_is_removed() -> None:
    assert validate_ai_response(f"\n\n{VALID_RESPONSE}\n\n") == VALID_RESPONSE.strip()


def test_reasoning_blocks_are_removed() -> None:
    """Regression: qwen3 emits <think> blocks that must not be stored."""

    response = f"<think>\n## Summary of my thoughts\nhmm\n</think>\n{VALID_RESPONSE}"

    assert validate_ai_response(response) == VALID_RESPONSE.strip()


def test_empty_response_is_rejected() -> None:
    with pytest.raises(InvalidAIResponseError, match="empty"):
        validate_ai_response("  ")


def test_missing_section_is_rejected() -> None:
    response = VALID_RESPONSE.replace("## Risks", "## Something else")

    with pytest.raises(InvalidAIResponseError, match="missing one or more required sections"):
        validate_ai_response(response)


def test_out_of_order_sections_are_rejected() -> None:
    response = "## Summary\nA\n## Risks\nB\n## Trends\nC\n## Recommendations\nD"

    with pytest.raises(InvalidAIResponseError, match="not in the required order"):
        validate_ai_response(response)


def test_empty_section_is_rejected() -> None:
    response = "## Summary\nA\n## Trends\n\n## Risks\nC\n## Recommendations\nD"

    with pytest.raises(InvalidAIResponseError, match=r"section '## Trends' is empty"):
        validate_ai_response(response)


def test_invalid_response_is_still_a_value_error() -> None:
    assert issubclass(InvalidAIResponseError, ValueError)


def test_extract_section_returns_only_that_section() -> None:
    assert (
        extract_section(VALID_RESPONSE, "Summary")
        == "The repository shows active project activity."
    )
    assert (
        extract_section(VALID_RESPONSE, "Recommendations")
        == "Continue monitoring project activity."
    )


def test_extract_section_of_a_missing_section_is_empty() -> None:
    assert extract_section("## Summary\nA", "Risks") == ""
