def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"La Volasfera" in response.data
    assert b"Cycle Explorer" in response.data
    assert b"Source code" in response.data
    assert b"Methodology" in response.data


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_project_information_pages_load(client):
    expected_text = {
        "/methodology": b"UTC-day boundaries",
        "/sources": b"The Degrees of the Zodiac Symbolized",
        "/licence": b"Harish Patel",
    }
    for path, text in expected_text.items():
        response = client.get(path)
        assert response.status_code == 200
        assert text in response.data


def test_complete_licence_text_is_served(client):
    response = client.get("/licence/text")

    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert b"GNU AFFERO GENERAL PUBLIC LICENSE" in response.data


def test_security_headers_are_applied(client):
    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_required_ephemeris_is_configured(monkeypatch, tmp_path):
    import app

    monkeypatch.setattr(app, "configure_ephemeris", lambda: tmp_path)

    application = app.create_app({"TESTING": True, "EPHEMERIS_REQUIRED": True})

    assert application.extensions["ephemeris_path"] == tmp_path


def fake_cycle_events():
    from datetime import datetime, timezone
    from types import SimpleNamespace

    station = SimpleNamespace(
        dt_utc=datetime(1980, 1, 2, tzinfo=timezone.utc),
        direction="R",
        position_degree="10CP20",
    )
    dates = [26, 27, 28, 29, 30, 31]
    events = [
        SimpleNamespace(
            projected_dt_utc=datetime(2026, 8, day, tzinfo=timezone.utc),
            source_station=station,
        )
        for day in dates
    ]
    events.extend(
        SimpleNamespace(
            projected_dt_utc=datetime(2026, 9, day, tzinfo=timezone.utc),
            source_station=station,
        )
        for day in (1, 2)
    )
    return events


def test_calculation_shows_four_converse_timelines(monkeypatch):
    import app

    monkeypatch.setattr(app, "generate_cycle_events", lambda *args, **kwargs: fake_cycle_events())
    application = app.create_app({"TESTING": True})
    response = application.test_client().post(
        "/", data={"reference": "1980-01-01T12:00", "anchor": "2026-08-30T12:00"}
    )

    assert response.status_code == 200
    assert b"Node Transit Converse" in response.data
    assert b"Secondary Progression" in response.data
    assert "Secondary converse cycle · 1 day represents 1 year".encode() in response.data
    assert b"Tertiary Progression" in response.data
    assert "Tertiary converse cycle · 1 day represents 1 lunar month".encode() in response.data
    assert b"Minor Progression" in response.data
    assert "Minor converse cycle · 1 lunar month represents 1 year".encode() in response.data
    assert b"Secondary Progression \xe2\x80\x94 Direct" not in response.data


def test_direct_switch_adds_three_comparison_timelines(monkeypatch):
    import app

    monkeypatch.setattr(app, "generate_cycle_events", lambda *args, **kwargs: fake_cycle_events())
    application = app.create_app({"TESTING": True})
    response = application.test_client().post(
        "/",
        data={"reference": "1980-01-01T12:00", "anchor": "2026-08-30T12:00", "show_direct": "on"},
    )

    assert response.status_code == 200
    assert b"Secondary Progression \xe2\x80\x94 Direct" in response.data
    assert "Secondary direct cycle · 1 day represents 1 year".encode() in response.data
    assert b"Tertiary Progression \xe2\x80\x94 Direct" in response.data
    assert "Tertiary direct cycle · 1 day represents 1 lunar month".encode() in response.data
    assert b"Minor Progression \xe2\x80\x94 Direct" in response.data
    assert "Minor direct cycle · 1 lunar month represents 1 year".encode() in response.data
    assert b"Node Transit Direct" not in response.data


def test_invalid_form_value_is_reported(client):
    response = client.post(
        "/", data={"reference": "not-a-date", "anchor": "2026-08-30T12:00"}
    )

    assert response.status_code == 200
    assert b"Unable to calculate" in response.data
