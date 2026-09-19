"""Collector worker: runs the collection pipeline once or on a fixed interval."""

import argparse
import logging
import signal
import threading
from collections.abc import Sequence

from prometheus_client import start_http_server

from devops_insights import __version__
from devops_insights.collectors.github import GitHubClient
from devops_insights.core.config import get_settings
from devops_insights.core.logging import configure_logging
from devops_insights.models import CollectionStatus, CollectionTrigger
from devops_insights.observability.metrics import initialize_application_metrics
from devops_insights.services.collection import run_collection

logger = logging.getLogger("devops_insights.worker")


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DevOps Insights collector.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single collection, print the result and exit with a status code.",
    )

    return parser.parse_args(argv)


def _run_once() -> int:
    client = GitHubClient.from_settings()

    try:
        summary = run_collection(CollectionTrigger.CLI, client)
    finally:
        client.close()

    print(
        f"Collection {summary.status}: "
        f"total={summary.total} succeeded={summary.succeeded} failed={summary.failed}"
    )

    return 0 if summary.status is CollectionStatus.SUCCEEDED else 1


def _run_forever() -> int:
    settings = get_settings()
    stop = threading.Event()

    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stop.set())

    initialize_application_metrics(settings.app_name, settings.app_env, __version__)
    start_http_server(settings.collector_metrics_port)
    logger.info(
        "Collector started: interval=%ss metrics_port=%d",
        settings.collection_interval_seconds,
        settings.collector_metrics_port,
    )

    if not settings.collection_on_startup:
        stop.wait(settings.collection_interval_seconds)

    while not stop.is_set():
        client = GitHubClient.from_settings()

        try:
            run_collection(CollectionTrigger.SCHEDULE, client)
        except Exception:
            logger.exception("Scheduled collection crashed.")
        finally:
            client.close()

        stop.wait(settings.collection_interval_seconds)

    logger.info("Collector stopped.")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m devops_insights.worker``."""

    arguments = _parse_arguments(argv)
    configure_logging()

    return _run_once() if arguments.once else _run_forever()


if __name__ == "__main__":
    raise SystemExit(main())
