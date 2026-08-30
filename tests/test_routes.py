def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"La Volasfera" in response.data
    assert b"Cycle Explorer" in response.data


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

