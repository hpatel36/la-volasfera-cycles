"""Flask entry point for La Volasfera Cycle Explorer."""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template

from calculations.ephemeris import configure_ephemeris


def environment_flag(name: str, default: bool = False) -> bool:
    """Read a conventional true/false environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    application = Flask(__name__)
    application.config.from_mapping(
        EPHEMERIS_REQUIRED=environment_flag("EPHEMERIS_REQUIRED"),
    )

    if test_config:
        application.config.from_mapping(test_config)

    if application.config["EPHEMERIS_REQUIRED"]:
        application.extensions["ephemeris_path"] = configure_ephemeris()

    @application.get("/")
    def index():
        return render_template("index.html")

    @application.get("/health")
    def health():
        return jsonify(status="ok")

    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
