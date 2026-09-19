import uuid

import pytest

from devops_insights import worker
from devops_insights.models import CollectionStatus, CollectionTrigger
from devops_insights.services.collection import CollectionSummary


@pytest.mark.parametrize(
    ("status", "exit_code"),
    [
        (CollectionStatus.SUCCEEDED, 0),
        (CollectionStatus.PARTIAL, 1),
        (CollectionStatus.FAILED, 1),
    ],
)
def test_once_reports_the_outcome_through_the_exit_code(
    monkeypatch, capsys, status, exit_code
) -> None:
    triggers: list[CollectionTrigger] = []

    def fake_run_collection(trigger, client):
        triggers.append(trigger)
        return CollectionSummary(uuid.uuid4(), status, total=3, succeeded=2, failed=1)

    monkeypatch.setattr(worker, "run_collection", fake_run_collection)

    assert worker.main(["--once"]) == exit_code
    assert triggers == [CollectionTrigger.CLI]
    assert f"Collection {status}: total=3 succeeded=2 failed=1" in capsys.readouterr().out
