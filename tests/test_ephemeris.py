import pytest

from calculations import ephemeris


def test_resolve_ephemeris_path_defaults_to_project_ephe(monkeypatch):
    monkeypatch.delenv(ephemeris.EPHEMERIS_ENVIRONMENT_VARIABLE, raising=False)

    assert ephemeris.resolve_ephemeris_path() == ephemeris.PROJECT_ROOT / "ephe"


def test_validate_ephemeris_files_rejects_missing_file(tmp_path):
    with pytest.raises(ephemeris.EphemerisConfigurationError, match="missing"):
        ephemeris.validate_ephemeris_files(tmp_path)


def test_validate_ephemeris_files_rejects_wrong_checksum(tmp_path, monkeypatch):
    candidate = tmp_path / "sample.se1"
    candidate.write_bytes(b"not ephemeris data")
    monkeypatch.setattr(
        ephemeris,
        "REQUIRED_EPHEMERIS_FILES",
        {candidate.name: "0" * 64},
    )

    with pytest.raises(ephemeris.EphemerisConfigurationError, match="SHA-256"):
        ephemeris.validate_ephemeris_files(tmp_path)


def test_configure_ephemeris_rejects_moshier_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(ephemeris, "resolve_ephemeris_path", lambda: tmp_path)
    monkeypatch.setattr(ephemeris, "validate_ephemeris_files", lambda path: None)
    monkeypatch.setattr(ephemeris.swe, "set_ephe_path", lambda path: None)
    monkeypatch.setattr(
        ephemeris.swe,
        "calc_ut",
        lambda *args: ((0.0,) * 6, ephemeris.swe.FLG_MOSEPH, ""),
    )

    with pytest.raises(ephemeris.EphemerisConfigurationError, match="fallback"):
        ephemeris.configure_ephemeris()


def test_configure_ephemeris_accepts_swiss_files(tmp_path, monkeypatch):
    configured_paths: list[str] = []
    monkeypatch.setattr(ephemeris, "resolve_ephemeris_path", lambda: tmp_path)
    monkeypatch.setattr(ephemeris, "validate_ephemeris_files", lambda path: None)
    monkeypatch.setattr(
        ephemeris.swe,
        "set_ephe_path",
        lambda path: configured_paths.append(path),
    )
    monkeypatch.setattr(
        ephemeris.swe,
        "calc_ut",
        lambda *args: ((0.0,) * 6, ephemeris.swe.FLG_SWIEPH, ""),
    )

    assert ephemeris.configure_ephemeris() == tmp_path
    assert configured_paths == [str(tmp_path)]
