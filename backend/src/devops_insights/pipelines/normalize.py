from devops_insights.schemas.github import GitHubRepositoryData


def _clean(value: str | None) -> str | None:
    """Strip surrounding whitespace and turn blank strings into ``None``."""

    if value is None:
        return None

    return value.strip() or None


def normalize_repository(data: GitHubRepositoryData) -> GitHubRepositoryData:
    """Return a copy of the repository data that is safe to persist."""

    return data.model_copy(
        update={
            "name": data.name.strip(),
            "full_name": data.full_name.strip(),
            "description": _clean(data.description),
            "default_branch": data.default_branch.strip(),
            "primary_language": _clean(data.primary_language),
            "license_name": _clean(data.license_name),
        }
    )
