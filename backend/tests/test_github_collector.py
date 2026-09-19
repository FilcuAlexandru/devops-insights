import httpx
import pytest

from devops_insights.collectors.github import GitHubClient, GitHubError, GitHubRateLimitError

PAYLOAD = {
    "name": "kubernetes",
    "full_name": "kubernetes/kubernetes",
    "description": "Container orchestration.",
    "html_url": "https://github.com/kubernetes/kubernetes",
    "default_branch": "master",
    "language": "Go",
    "license": {"name": "Apache License 2.0"},
    "archived": False,
    "stargazers_count": 120000,
    "forks_count": 42000,
    "open_issues_count": 2100,
    "created_at": "2014-06-06T22:56:04Z",
    "updated_at": "2026-09-01T10:00:00Z",
    "pushed_at": "2026-09-01T09:00:00Z",
}


def make_client(handler, token: str | None = None) -> GitHubClient:
    return GitHubClient(
        base_url="https://api.github.test",
        token=token,
        transport=httpx.MockTransport(handler),
    )


def test_fetch_repository_maps_the_github_payload() -> None:
    client = make_client(lambda request: httpx.Response(200, json=PAYLOAD))

    data = client.fetch_repository("kubernetes/kubernetes")

    assert data.full_name == "kubernetes/kubernetes"
    assert str(data.url) == "https://github.com/kubernetes/kubernetes"
    assert data.primary_language == "Go"
    assert data.license_name == "Apache License 2.0"
    assert (data.stars, data.forks, data.open_issues) == (120000, 42000, 2100)
    assert data.created_at.year == 2014
    assert data.pushed_at is not None


def test_fetch_repository_requests_the_expected_endpoint_and_headers() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=PAYLOAD)

    make_client(handler, token="secret").fetch_repository("kubernetes/kubernetes")

    request = seen[0]
    assert request.url.path == "/repos/kubernetes/kubernetes"
    assert request.headers["Authorization"] == "Bearer secret"
    assert request.headers["Accept"] == "application/vnd.github+json"


def test_requests_are_unauthenticated_without_a_token() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=PAYLOAD)

    make_client(handler).fetch_repository("kubernetes/kubernetes")

    assert "Authorization" not in seen[0].headers


def test_missing_optional_fields_are_accepted() -> None:
    payload = {**PAYLOAD, "language": None, "license": None, "description": None}
    payload.pop("pushed_at")
    client = make_client(lambda request: httpx.Response(200, json=payload))

    data = client.fetch_repository("kubernetes/kubernetes")

    assert data.primary_language is None
    assert data.license_name is None
    assert data.pushed_at is None


def test_not_found_is_reported_clearly() -> None:
    client = make_client(lambda request: httpx.Response(404, json={"message": "Not Found"}))

    with pytest.raises(GitHubError, match="'ghost/repo' was not found"):
        client.fetch_repository("ghost/repo")


def test_rate_limit_is_reported_with_reset_time() -> None:
    headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1789813224"}
    client = make_client(lambda request: httpx.Response(403, headers=headers))

    with pytest.raises(GitHubRateLimitError, match="Resets at .*GITHUB_TOKEN"):
        client.fetch_repository("kubernetes/kubernetes")


def test_forbidden_without_exhausted_rate_limit_is_a_plain_error() -> None:
    client = make_client(lambda request: httpx.Response(403))

    with pytest.raises(GitHubError, match="HTTP 403") as error:
        client.fetch_repository("kubernetes/kubernetes")

    assert not isinstance(error.value, GitHubRateLimitError)


def test_server_error_is_reported() -> None:
    client = make_client(lambda request: httpx.Response(503))

    with pytest.raises(GitHubError, match="HTTP 503"):
        client.fetch_repository("kubernetes/kubernetes")


def test_network_failure_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(GitHubError, match="Unable to reach the GitHub API"):
        make_client(handler).fetch_repository("kubernetes/kubernetes")


def test_unexpected_payload_is_rejected() -> None:
    client = make_client(lambda request: httpx.Response(200, json={"name": "only-a-name"}))

    with pytest.raises(GitHubError, match="Unexpected GitHub response"):
        client.fetch_repository("kubernetes/kubernetes")
