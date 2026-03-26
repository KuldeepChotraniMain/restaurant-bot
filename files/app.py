"""
app.py — Flask application factory
"""

import os

from flask import Flask, jsonify, send_from_directory

from config import Config
from database import close_db
from models import init_db
from routes.admin import admin_bp
from routes.public import public_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=Config.STATIC_FOLDER,
        static_url_path="",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"]  = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Admin-Token"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    @app.before_request
    def handle_preflight():
        from flask import request
        if request.method == "OPTIONS":
            return jsonify({}), 200

    # ── DB teardown ───────────────────────────────────────────────────────────
    app.teardown_appcontext(close_db)

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    # ── SPA catch-all ─────────────────────────────────────────────────────────
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path: str):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    # ── Database init (runs once at startup) ──────────────────────────────────
    with app.app_context():
        init_db()

    return app
