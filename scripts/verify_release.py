"""Run a strict, deployment-oriented application smoke test."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ephe-path",
        type=Path,
        required=True,
        help="Directory containing the two pinned Swiss Ephemeris files.",
    )
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    arguments = parse_arguments()
    os.environ["SE_EPHE_PATH"] = str(arguments.ephe_path.resolve())
    os.environ["EPHEMERIS_REQUIRED"] = "true"

    # Import only after strict deployment environment variables are set.
    from app import app

    require(not app.debug, "application debug mode must be disabled")
    require("ephemeris_path" in app.extensions, "strict ephemeris setup did not run")

    client = app.test_client()
    health = client.get("/health")
    require(health.status_code == 200, "health endpoint failed")
    require(health.get_json() == {"status": "ok"}, "health response was unexpected")

    for path in ("/", "/methodology", "/sources", "/licence", "/licence/text"):
        response = client.get(path)
        require(response.status_code == 200, f"GET {path} failed")

    calculation = client.post(
        "/",
        data={
            "reference": "1980-01-01T12:00",
            "anchor": "2026-08-30T12:00",
            "show_direct": "on",
        },
    )
    require(calculation.status_code == 200, "calculation request failed")
    require(b"Node Transit Converse" in calculation.data, "transit result is missing")
    require(b"Minor Progression \xe2\x80\x94 Direct" in calculation.data, "direct result is missing")
    require(b"Unable to calculate" not in calculation.data, "calculation returned an error")
    require(
        calculation.headers.get("X-Content-Type-Options") == "nosniff",
        "security headers are missing",
    )

    print("Release smoke test passed: strict ephemeris startup, routes and calculation.")


if __name__ == "__main__":
    main()
