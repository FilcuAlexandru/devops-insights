import logging
import time
from uuid import UUID

from sqlalchemy.orm import Session

from devops_insights.ai.context import build_repository_context
from devops_insights.ai.errors import InvalidAIResponseError
from devops_insights.ai.ollama import generate_response
from devops_insights.ai.persistence import save_ai_analysis
from devops_insights.ai.prompts import build_repository_analysis_prompt
from devops_insights.ai.response import validate_ai_response
from devops_insights.models import AIAnalysis
from devops_insights.observability.metrics import record_ai_analysis, record_ai_analysis_error

logger = logging.getLogger(__name__)

# Small local models occasionally ignore the required format, so one retry is allowed.
MAX_ATTEMPTS = 2


def _generate_valid_response(prompt: str) -> str:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return validate_ai_response(generate_response(prompt))
        except InvalidAIResponseError as exc:
            logger.warning("Invalid AI response (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)

            if attempt == MAX_ATTEMPTS:
                raise

    raise AssertionError("unreachable")


def analyze_repository(session: Session, repository_id: UUID) -> AIAnalysis | None:
    """Analyze a repository with Ollama and persist the result.

    Returns ``None`` when the repository does not exist.
    """

    context = build_repository_context(session, repository_id)

    if context is None:
        return None

    prompt = build_repository_analysis_prompt(context)
    started = time.perf_counter()

    try:
        response = _generate_valid_response(prompt)
    except Exception:
        record_ai_analysis_error()
        raise

    analysis = save_ai_analysis(
        session=session,
        repository_id=repository_id,
        context=context,
        prompt=prompt,
        response=response,
    )

    record_ai_analysis(time.perf_counter() - started)

    return analysis
