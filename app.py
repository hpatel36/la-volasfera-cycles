"""Flask entry point for La Volasfera Cycle Explorer."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from calculations.cycles import generate_cycle_events
from calculations.degree_definitions import lookup_la_volasfera
from calculations.ephemeris import configure_ephemeris


UTC = timezone.utc
PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_CODE_URL = "https://github.com/hpatel36/la-volasfera-cycles"
TIMELINE_SPECS = (
    {
        "label": "Node Transit Converse",
        "description": "True Node stations mirrored around the reference time.",
        "method": "transit",
        "converse": True,
        "primary": True,
    },
    {
        "label": "Secondary Progression — Converse",
        "description": "Secondary converse cycle · 1 day represents 1 year.",
        "method": "secondary",
        "converse": True,
        "primary": True,
    },
    {
        "label": "Tertiary Progression — Converse",
        "description": "Tertiary converse cycle · 1 lunar month represents 1 year.",
        "method": "tertiary",
        "converse": True,
        "primary": True,
    },
    {
        "label": "Minor Progression — Converse",
        "description": "Minor converse cycle · the monthly-to-yearly ratio.",
        "method": "minor",
        "converse": True,
        "primary": True,
    },
    {
        "label": "Secondary Progression — Direct",
        "description": "Secondary direct cycle · shown for comparison.",
        "method": "secondary",
        "converse": False,
        "primary": False,
    },
    {
        "label": "Tertiary Progression — Direct",
        "description": "Tertiary direct cycle · shown for comparison.",
        "method": "tertiary",
        "converse": False,
        "primary": False,
    },
    {
        "label": "Minor Progression — Direct",
        "description": "Minor direct cycle · shown for comparison.",
        "method": "minor",
        "converse": False,
        "primary": False,
    },
)


def environment_flag(name: str, default: bool = False) -> bool:
    """Read a conventional true/false environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_utc_datetime(value: str, field_label: str) -> datetime:
    """Parse an HTML datetime-local value and explicitly treat it as UTC."""
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Enter a valid {field_label.lower()}.") from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def format_input_datetime(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M")


def build_timeline_results(reference_utc, anchor_utc, *, show_direct: bool) -> list[dict]:
    """Generate primary converse timelines and optional direct comparisons."""
    results = []
    for specification in TIMELINE_SPECS:
        if not specification["primary"] and not show_direct:
            continue
        events = generate_cycle_events(
            reference_utc,
            anchor_utc,
            method=str(specification["method"]),
            converse=bool(specification["converse"]),
        )
        nearest = min(
            events,
            key=lambda event: abs((event.projected_dt_utc - anchor_utc).total_seconds()),
        )
        results.append({**specification, "events": events, "nearest": nearest})
    return results


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    application = Flask(__name__)
    application.config.from_mapping(
        EPHEMERIS_REQUIRED=environment_flag("EPHEMERIS_REQUIRED"),
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    if test_config:
        application.config.from_mapping(test_config)

    if application.config["EPHEMERIS_REQUIRED"]:
        application.extensions["ephemeris_path"] = configure_ephemeris()

    application.jinja_env.globals["degree_definition"] = lookup_la_volasfera
    application.jinja_env.globals["source_code_url"] = SOURCE_CODE_URL

    @application.after_request
    def add_security_headers(response):
        """Apply conservative browser protections to every response."""
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'none'; object-src 'none'"
        )
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = (
            "camera=(), geolocation=(), microphone=(), payment=()"
        )
        return response

    @application.route("/", methods=["GET", "POST"])
    def index():
        now_utc = datetime.now(UTC).replace(second=0, microsecond=0)
        form_values = {
            "reference": "",
            "anchor": format_input_datetime(now_utc),
            "show_direct": False,
        }
        timelines = None
        error_message = None

        if request.method == "POST":
            form_values = {
                "reference": request.form.get("reference", "").strip(),
                "anchor": request.form.get("anchor", "").strip(),
                "show_direct": request.form.get("show_direct") == "on",
            }
            try:
                reference_utc = parse_utc_datetime(
                    str(form_values["reference"]),
                    "Reference date and time",
                )
                anchor_utc = parse_utc_datetime(
                    str(form_values["anchor"]),
                    "Anchor date and time",
                )
                timelines = build_timeline_results(
                    reference_utc,
                    anchor_utc,
                    show_direct=bool(form_values["show_direct"]),
                )
            except (ValueError, OverflowError) as error:
                error_message = str(error)

        return render_template(
            "index.html",
            form_values=form_values,
            timelines=timelines,
            error_message=error_message,
        )

    @application.get("/health")
    def health():
        return jsonify(status="ok")

    @application.get("/methodology")
    def methodology():
        return render_template("information.html", page="methodology")

    @application.get("/sources")
    def sources():
        return render_template("information.html", page="sources")

    @application.get("/licence")
    def licence():
        return render_template("information.html", page="licence")

    @application.get("/licence/text")
    def licence_text():
        return send_file(PROJECT_ROOT / "LICENSE", mimetype="text/plain")

    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
