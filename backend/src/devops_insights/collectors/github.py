import logging
from datetime import UTC, datetime

import httpx
from pydantic import ValidationError

from devops_insights.core.config import Settings, get_settings
from devops_insights.schemas.github import GitHubRepositoryData

logger = logging.getLogger(__name__)

GITHUB_API_VERSION = "2022-11-28"


class GitHubError(RuntimeError):
    """A GitHub API request failed."""


class GitHubRateLimitError(GitHubError):
    """The GitHub API rate limit has been exhausted."""


class GitHubClient:
    """Minimal read-only client for the public GitHub REST API."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "DevOps-Insights",
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "GitHubClient":
        """Create a client configured from application settings."""

        settings = settings or get_settings()

        return cls(
            base_url=settings.github_api_url,
            token=settings.github_token,
            timeout=settings.github_timeout,
        )

    def close(self) -> None:
        """Release the underlying HTTP connections."""

        self._client.close()

    def fetch_repository(self, full_name: str) -> GitHubRepositoryData:
        """Fetch and validate a repository given as ``owner/name``."""

        try:
            response = self._client.get(f"/repos/{full_name}")
        except httpx.HTTPError as exc:
            raise GitHubError(f"Unable to reach the GitHub API: {exc}") from exc

        self._raise_for_status(response, full_name)

        return self._parse_repository(response.json(), full_name)

    @staticmethod
    def _raise_for_status(response: httpx.Response, full_name: str) -> None:
        if response.is_success:
            return

        if response.headers.get("x-ratelimit-remaining") == "0" and response.status_code in (
            403,
            429,
        ):
            reset = response.headers.get("x-ratelimit-reset")
            hint = "Set GITHUB_TOKEN to raise the limit."

            if reset and reset.isdigit():
                reset_at = datetime.fromtimestamp(int(reset), UTC).strftime("%H:%M:%S UTC")
                hint = f"Resets at {reset_at}. {hint}"

            raise GitHubRateLimitError(f"GitHub API rate limit exceeded. {hint}")

        if response.status_code == 404:
            raise GitHubError(f"Repository '{full_name}' was not found on GitHub.")

        raise GitHubError(
            f"GitHub API request for '{full_name}' failed with HTTP {response.status_code}."
        )

    @staticmethod
    def _parse_repository(payload: dict, full_name: str) -> GitHubRepositoryData:
        license_info = payload.get("license") or {}

        try:
            return GitHubRepositoryData(
                name=payload["name"],
                full_name=payload["full_name"],
                description=payload.get("description"),
                url=payload["html_url"],
                default_branch=payload["default_branch"],
                primary_language=payload.get("language"),
                license_name=license_info.get("name"),
                archived=payload.get("archived", False),
                stars=payload["stargazers_count"],
                forks=payload["forks_count"],
                open_issues=payload["open_issues_count"],
                created_at=payload["created_at"],
                updated_at=payload["updated_at"],
                pushed_at=payload.get("pushed_at"),
            )
        except (KeyError, ValidationError) as exc:
            raise GitHubError(f"Unexpected GitHub response for '{full_name}': {exc}") from exc
