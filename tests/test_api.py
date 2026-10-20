from fastapi.testclient import TestClient


def test_seed_convert_flow(client: TestClient) -> None:
    seeded = client.post("/seed", params={"count": 5}).json()
    assert len(seeded) == 5

    assert client.post("/convert").json() == {"converted": 5}
    assert client.post("/convert").json() == {"converted": 0}

    numbers = client.get("/numbers").json()
    words = client.get("/words").json()
    assert [w["number_id"] for w in words] == [n["id"] for n in numbers]


def test_seed_rejects_invalid_count(client: TestClient) -> None:
    assert client.post("/seed", params={"count": 0}).status_code == 422
