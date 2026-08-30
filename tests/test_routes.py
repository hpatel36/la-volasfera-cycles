def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"La Volasfera" in response.data
    assert b"Cycle Explorer" in response.data


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_required_ephemeris_is_configured(monkeypatch, tmp_path):
    import app

    monkeypatch.setattr(app, "configure_ephemeris", lambda: tmp_path)

    application = app.create_app({"TESTING": True, "EPHEMERIS_REQUIRED": True})

    assert application.extensions["ephemeris_path"] == tmp_path
