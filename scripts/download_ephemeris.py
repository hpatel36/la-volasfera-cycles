"""Download the pinned Swiss Ephemeris files required by this application."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from calculations.ephemeris import (  # noqa: E402
    PINNED_SWISS_EPHEMERIS_COMMIT,
    REQUIRED_EPHEMERIS_FILES,
    file_sha256,
)


DOWNLOAD_ROOT = (
    "https://raw.githubusercontent.com/aloistr/swisseph/"
    f"{PINNED_SWISS_EPHEMERIS_COMMIT}/ephe"
)


def download_file(url: str, destination: Path, expected_digest: str) -> None:
    """Download one file atomically and accept it only if its digest matches."""
    if destination.is_file() and file_sha256(destination) == expected_digest:
        print(f"Verified existing {destination.name}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".download",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)

    try:
        print(f"Downloading {destination.name}")
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "LaVolasferaCycles-build"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Download of {destination.name} returned HTTP {response.status}"
                )
            with temporary_path.open("wb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block)

        actual_digest = file_sha256(temporary_path)
        if actual_digest != expected_digest:
            raise RuntimeError(
                f"SHA-256 mismatch for {destination.name}: {actual_digest}"
            )
        temporary_path.replace(destination)
        print(f"Verified downloaded {destination.name}")
    finally:
        temporary_path.unlink(missing_ok=True)


def download_ephemeris(destination: Path) -> None:
    """Download every ephemeris file in the pinned application manifest."""
    for filename, expected_digest in REQUIRED_EPHEMERIS_FILES.items():
        download_file(
            f"{DOWNLOAD_ROOT}/{filename}",
            destination / filename,
            expected_digest,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--destination",
        type=Path,
        default=PROJECT_ROOT / "ephe",
        help="directory in which to place the .se1 files",
    )
    arguments = parser.parse_args()
    download_ephemeris(arguments.destination.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
