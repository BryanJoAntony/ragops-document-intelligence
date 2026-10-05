from app.utils.ids import new_request_id


def test_new_request_id_has_prefix() -> None:
    request_id = new_request_id()

    assert request_id.startswith("req_")
    assert len(request_id) > len("req_")


def test_new_request_id_custom_prefix() -> None:
    request_id = new_request_id(prefix="job")

    assert request_id.startswith("job_")