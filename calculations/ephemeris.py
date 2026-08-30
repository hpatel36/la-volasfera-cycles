"""Swiss Ephemeris data-file configuration and validation."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import swisseph as swe


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EPHEMERIS_ENVIRONMENT_VARIABLE = "SE_EPHE_PATH"
PINNED_SWISS_EPHEMERIS_COMMIT = "b51a083390bf3cdc93a6ba466cbc83b846c4cfc4"
REQUIRED_EPHEMERIS_FILES = {
    "semo_12.se1": "ddf9263fc2bacf47b4d2a275cfa88d1a6c6467a7d4789ab10199f2743611f374",
    "semo_18.se1": "ecfa54dbf5bc0b5a9bc3e04ed28629a821e98625eacae38f4070593bba0e2980",
}
PROBE_JULIAN_DAYS = (
    swe.julday(1400, 6, 1, 0.0, swe.GREG_CAL),
    swe.julday(2100, 6, 1, 0.0, swe.GREG_CAL),
)


class EphemerisConfigurationError(RuntimeError):
    """Raised when the required Swiss Ephemeris data is unavailable or invalid."""


def resolve_ephemeris_path() -> Path:
    """Return the configured ephemeris directory as an absolute path."""
    configured = os.environ.get(EPHEMERIS_ENVIRONMENT_VARIABLE, "ephe")
    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def file_sha256(path: Path) -> str:
    """Calculate a file's SHA-256 digest without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_ephemeris_files(path: Path) -> None:
    """Require the two pinned lunar ephemeris files and their exact contents."""
    if not path.is_dir():
        raise EphemerisConfigurationError(
            f"Swiss Ephemeris directory does not exist: {path}"
        )

    for filename, expected_digest in REQUIRED_EPHEMERIS_FILES.items():
        candidate = path / filename
        if not candidate.is_file():
            raise EphemerisConfigurationError(
                f"Required Swiss Ephemeris file is missing: {candidate}"
            )
        actual_digest = file_sha256(candidate)
        if actual_digest != expected_digest:
            raise EphemerisConfigurationError(
                f"Swiss Ephemeris file failed SHA-256 validation: {candidate}"
            )


def configure_ephemeris() -> Path:
    """Validate, configure and probe Swiss Ephemeris across the supported range."""
    path = resolve_ephemeris_path()
    validate_ephemeris_files(path)
    swe.set_ephe_path(str(path))

    requested_flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    for julian_day in PROBE_JULIAN_DAYS:
        _, returned_flags, error = swe.calc_ut(
            julian_day,
            swe.TRUE_NODE,
            requested_flags,
        )
        if error:
            raise EphemerisConfigurationError(
                f"Swiss Ephemeris probe failed: {error.strip()}"
            )
        if not returned_flags & swe.FLG_SWIEPH:
            raise EphemerisConfigurationError(
                "Swiss Ephemeris probe used a fallback instead of the required .se1 files"
            )

    return path
