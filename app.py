"""Flask entry point for La Volasfera Cycle Explorer."""

from flask import Flask, jsonify, render_template


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    application = Flask(__name__)

    if test_config:
        application.config.from_mapping(test_config)

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

