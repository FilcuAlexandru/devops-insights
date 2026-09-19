import re

from sqlalchemy import func, select

from devops_insights.catalog import CATALOG, TechnologyDefinition
from devops_insights.models import Technology
from devops_insights.services.catalog import sync_catalog

FULL_NAME_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")


def test_catalog_slugs_are_unique() -> None:
    slugs = [entry.slug for entry in CATALOG]

    assert len(slugs) == len(set(slugs))


def test_catalog_repositories_are_unique_and_well_formed() -> None:
    repositories = [name for entry in CATALOG for name in entry.repositories]

    assert repositories
    assert len(repositories) == len(set(repositories))
    assert all(FULL_NAME_PATTERN.match(name) for name in repositories)


def test_every_catalog_entry_is_fully_described() -> None:
    for entry in CATALOG:
        assert entry.repositories, entry.slug
        assert entry.description, entry.slug
        assert entry.website_url.startswith("https://"), entry.slug


def test_sync_catalog_creates_all_technologies(session) -> None:
    technologies = sync_catalog(session)

    assert set(technologies) == {entry.slug for entry in CATALOG}
    assert session.scalar(select(func.count(Technology.id))) == len(CATALOG)


def test_sync_catalog_is_idempotent(session) -> None:
    sync_catalog(session)
    sync_catalog(session)

    assert session.scalar(select(func.count(Technology.id))) == len(CATALOG)


def test_sync_catalog_updates_existing_technologies(session) -> None:
    original = TechnologyDefinition("demo", "Demo", "testing", "First.", "https://a.test", ("a/b",))
    changed = TechnologyDefinition("demo", "Demo 2", "other", "Second.", "https://b.test", ("a/b",))

    first = sync_catalog(session, [original])["demo"]
    second = sync_catalog(session, [changed])["demo"]

    assert second.id == first.id
    assert (second.name, second.category, second.description) == ("Demo 2", "other", "Second.")
    assert second.website_url == "https://b.test"
