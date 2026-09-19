from devops_insights.analytics.dashboard import build_dashboard
from tests.factories import add_snapshot, make_repository, make_technology


def seed(session):
    kubernetes = make_technology(session, "kubernetes", name="Kubernetes")
    docker = make_technology(session, "docker", name="Docker")

    main = make_repository(
        session, kubernetes, "k/main", stars=1000, forks=100, open_issues=10, primary_language="Go"
    )
    side = make_repository(
        session, kubernetes, "k/side", stars=300, forks=30, open_issues=3, primary_language="Go"
    )
    engine = make_repository(
        session, docker, "d/engine", stars=500, forks=50, open_issues=5, primary_language=None
    )

    return main, side, engine


def test_empty_database_yields_an_empty_dashboard(session) -> None:
    dashboard = build_dashboard(session)

    assert dashboard.totals.repositories == 0
    assert dashboard.totals.stars == 0
    assert dashboard.technologies == []
    assert dashboard.top_repositories == []
    assert dashboard.last_collection is None


def test_totals_add_up_all_repositories(session) -> None:
    main, _, _ = seed(session)
    add_snapshot(session, main, days=0, stars=900)
    add_snapshot(session, main, days=1, stars=1000)

    totals = build_dashboard(session).totals

    assert totals.technologies == 2
    assert totals.repositories == 3
    assert totals.stars == 1800
    assert totals.forks == 180
    assert totals.open_issues == 18
    assert totals.snapshots == 2


def test_technology_shares_are_ranked_by_stars(session) -> None:
    seed(session)

    shares = build_dashboard(session).technologies

    assert [(share.slug, share.repository_count, share.stars) for share in shares] == [
        ("kubernetes", 2, 1300),
        ("docker", 1, 500),
    ]


def test_languages_group_unknown_values(session) -> None:
    seed(session)

    languages = {
        share.language: share.repository_count for share in build_dashboard(session).languages
    }

    assert languages == {"Go": 2, "Unknown": 1}


def test_top_repositories_are_ordered_by_stars(session) -> None:
    seed(session)

    names = [item.full_name for item in build_dashboard(session).top_repositories]

    assert names == ["k/main", "d/engine", "k/side"]


def test_filtering_by_technology_limits_every_figure(session) -> None:
    seed(session)

    dashboard = build_dashboard(session, "docker")

    assert dashboard.totals.repositories == 1
    assert dashboard.totals.stars == 500
    assert [share.slug for share in dashboard.technologies] == ["docker"]
    assert [item.full_name for item in dashboard.top_repositories] == ["d/engine"]


def test_fastest_growing_needs_at_least_two_snapshots(session) -> None:
    main, side, engine = seed(session)
    add_snapshot(session, main, days=0, stars=900)
    add_snapshot(session, main, days=10, stars=1000)
    add_snapshot(session, side, days=0, stars=290)
    add_snapshot(session, side, days=5, stars=300)
    add_snapshot(session, engine, days=0, stars=500)

    growing = build_dashboard(session).fastest_growing

    assert [(item.full_name, item.stars_gained) for item in growing] == [
        ("k/main", 100),
        ("k/side", 10),
    ]
    assert growing[0].stars_per_day == 10.0


def test_shrinking_repositories_are_not_listed_as_growing(session) -> None:
    main, _, _ = seed(session)
    add_snapshot(session, main, days=0, stars=1100)
    add_snapshot(session, main, days=1, stars=1000)

    assert build_dashboard(session).fastest_growing == []
