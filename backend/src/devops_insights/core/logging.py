import logging

from devops_insights.core.config import get_settings


def configure_logging() -> None:
    """Configure application-wide logging."""

    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # httpx logs every outgoing request at INFO, which drowns the application's own messages.
    logging.getLogger("httpx").setLevel(logging.WARNING)
