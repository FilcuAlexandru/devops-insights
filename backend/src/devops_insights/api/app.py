from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from devops_insights import __version__
from devops_insights.api.routes import (
    ai,
    collection,
    dashboard,
    health,
    repositories,
    system,
    technologies,
)
from devops_insights.core.config import get_settings
from devops_insights.core.logging import configure_logging
from devops_insights.observability.metrics import initialize_application_metrics

ROUTERS = (
    health.router,
    system.router,
    dashboard.router,
    technologies.router,
    repositories.router,
    collection.router,
    ai.router,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Collects, stores and analyzes public DevOps ecosystem data.",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    for router in ROUTERS:
        app.include_router(router)

    initialize_application_metrics(
        app_name=settings.app_name,
        environment=settings.app_env,
        version=__version__,
    )

    Instrumentator(excluded_handlers=["/metrics", "/health", "/health/ready"]).instrument(
        app
    ).expose(app, include_in_schema=False)

    return app
