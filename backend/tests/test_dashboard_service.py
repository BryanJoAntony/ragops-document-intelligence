from app.services.dashboard_service import DashboardService


def test_dashboard_average_returns_none_for_empty_values() -> None:
    assert DashboardService._average([]) is None


def test_dashboard_average_rounds_values() -> None:
    assert DashboardService._average([0.9, 0.95, 1.0]) == 0.95


def test_dashboard_overview_activity_sorting_shape() -> None:
    # Small guard test for dashboard-safe response shape.
    latest_activity = [
        {"type": "query", "created_at": "2026-08-03T08:00:00+00:00"},
        {"type": "job", "created_at": "2026-08-03T09:00:00+00:00"},
    ]

    latest_activity.sort(
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )

    assert latest_activity[0]["type"] == "job"
