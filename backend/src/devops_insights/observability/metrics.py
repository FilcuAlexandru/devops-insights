import time

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import Engine, event

_LONG_OPERATION_BUCKETS = (0.5, 1, 2.5, 5, 10, 30, 60, 120, 300, 600)
_DATABASE_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5)

application_info = Gauge(
    "devops_insights_application_info",
    "Static information about the DevOps Insights application.",
    ["app_name", "environment", "version"],
)

repositories_collected_total = Counter(
    "devops_insights_repositories_collected_total",
    "Total number of repositories successfully collected.",
)

collection_errors_total = Counter(
    "devops_insights_collection_errors_total",
    "Total number of repository collection errors.",
)

collection_runs_total = Counter(
    "devops_insights_collection_runs_total",
    "Total number of finished collection runs.",
    ["status"],
)

collection_duration_seconds = Histogram(
    "devops_insights_collection_duration_seconds",
    "Duration of a full collection run.",
    buckets=_LONG_OPERATION_BUCKETS,
)

collection_last_success_timestamp_seconds = Gauge(
    "devops_insights_collection_last_success_timestamp_seconds",
    "Unix time of the last collection run that finished without failures.",
)

ai_analyses_total = Counter(
    "devops_insights_ai_analyses_total",
    "Total number of AI repository analyses generated.",
)

ai_analysis_errors_total = Counter(
    "devops_insights_ai_analysis_errors_total",
    "Total number of failed AI repository analyses.",
)

ai_analysis_duration_seconds = Histogram(
    "devops_insights_ai_analysis_duration_seconds",
    "Duration of generating an AI repository analysis.",
    buckets=_LONG_OPERATION_BUCKETS,
)

database_query_duration_seconds = Histogram(
    "devops_insights_database_query_duration_seconds",
    "Duration of individual database statements.",
    buckets=_DATABASE_BUCKETS,
)


def initialize_application_metrics(app_name: str, environment: str, version: str) -> None:
    """Publish static application information."""

    application_info.labels(app_name=app_name, environment=environment, version=version).set(1)


def instrument_database_engine(engine: Engine) -> None:
    """Record the duration of every statement executed through the engine."""

    @event.listens_for(engine, "before_cursor_execute")
    def _start_timer(connection, cursor, statement, parameters, context, executemany):
        connection.info.setdefault("query_start_times", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def _stop_timer(connection, cursor, statement, parameters, context, executemany):
        started = connection.info["query_start_times"].pop()
        database_query_duration_seconds.observe(time.perf_counter() - started)


def record_repository_collected() -> None:
    """Record a successfully collected repository."""

    repositories_collected_total.inc()


def record_collection_error() -> None:
    """Record a repository collection error."""

    collection_errors_total.inc()


def record_collection_run(status: str, duration_seconds: float) -> None:
    """Record a finished collection run."""

    collection_runs_total.labels(status=status).inc()
    collection_duration_seconds.observe(duration_seconds)

    if status == "succeeded":
        collection_last_success_timestamp_seconds.set_to_current_time()


def record_ai_analysis(duration_seconds: float) -> None:
    """Record a generated AI analysis."""

    ai_analyses_total.inc()
    ai_analysis_duration_seconds.observe(duration_seconds)


def record_ai_analysis_error() -> None:
    """Record a failed AI analysis."""

    ai_analysis_errors_total.inc()
