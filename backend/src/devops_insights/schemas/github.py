from datetime import datetime

from pydantic import BaseModel, HttpUrl


class GitHubRepositoryData(BaseModel):
    """Repository data extracted from the GitHub API."""

    name: str
    full_name: str
    description: str | None
    url: HttpUrl
    default_branch: str
    primary_language: str | None
    license_name: str | None
    archived: bool
    stars: int
    forks: int
    open_issues: int
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None
