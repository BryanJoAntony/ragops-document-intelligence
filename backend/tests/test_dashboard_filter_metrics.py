from app.services.dashboard_service import DashboardService


def test_dashboard_filter_usage_counts_ignores_empty_filters() -> None:
    service = DashboardService.__new__(DashboardService)

    class FakeQuery:
        def __init__(self, rows):
            self.rows = rows

        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return self.rows

    class FakeDb:
        def query(self, *args, **kwargs):
            return FakeQuery([
                ({},),
                ({"filename": "sample.txt"},),
                ({"filename": "sample.txt", "language": "en"},),
                ({"parser_name": None},),
            ])

    service.db = FakeDb()

    counts = service._build_filter_usage_counts()

    assert counts == {
        "filename": 2,
        "language": 1,
    }
