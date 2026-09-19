import re

from devops_insights.ai.errors import InvalidAIResponseError

REQUIRED_SECTIONS = (
    "## Summary",
    "## Trends",
    "## Risks",
    "## Recommendations",
)

_REASONING_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def validate_ai_response(response: str) -> str:
    """Validate and normalize an AI repository analysis.

    Reasoning blocks emitted by some models are removed. The response must contain
    every required section, in order, each with content.
    """

    if not response or not response.strip():
        raise InvalidAIResponseError("AI response is empty.")

    normalized = _REASONING_BLOCK.sub("", response).strip()

    positions = [normalized.find(section) for section in REQUIRED_SECTIONS]

    if any(position == -1 for position in positions):
        raise InvalidAIResponseError("AI response is missing one or more required sections.")

    if positions != sorted(positions):
        raise InvalidAIResponseError("AI response sections are not in the required order.")

    for section in REQUIRED_SECTIONS:
        if not extract_section(normalized, section.removeprefix("## ")):
            raise InvalidAIResponseError(f"AI response section '{section}' is empty.")

    return normalized


def extract_section(response: str, title: str) -> str:
    """Return the text of one ``## <title>`` section, or an empty string."""

    match = re.search(
        rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)",
        response,
        flags=re.MULTILINE | re.DOTALL,
    )

    return match.group(1).strip() if match else ""
