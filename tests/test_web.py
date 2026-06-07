from fastapi.testclient import TestClient

from app.main import create_app


def test_trip_list_page_loads() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "出游记录" in response.text
