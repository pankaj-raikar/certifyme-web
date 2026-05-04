import os
from flask import Flask, jsonify, send_from_directory
from app.config import DevelopmentConfig, ProductionConfig
from app.extensions import db, migrate, login_manager, cors
from app.models import Admin


def create_app(config_class=None):
    """App factory — initialize Flask with extensions & blueprints."""
    # Auto-detect production config if not specified
    if config_class is None:
        config_class = (
            ProductionConfig
            if os.getenv("FLASK_ENV") == "production"
            else DevelopmentConfig
        )

    # In production, serve frontend from static folder
    static_folder = (
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        if os.getenv("FLASK_ENV") == "production"
        else None
    )

    app = Flask(__name__, static_folder=static_folder, static_url_path="")
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configure CORS based on environment
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "")
    if os.getenv("FLASK_ENV") == "production":
        # In production, allow the configured frontend origin or same-origin
        cors_origins = [frontend_origin] if frontend_origin else []
        # Also allow requests from same host (when frontend is served by Flask)
        cors_origins.append("*")  # For same-origin when Flask serves frontend
    else:
        # Development CORS origins
        cors_origins = ["http://127.0.0.1:5500", "http://localhost:5500"]

    cors.init_app(
        app,
        origins=cors_origins,
        supports_credentials=True,
    )

    # Login manager config
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        """Load admin by ID when Flask-Login needs it."""
        return Admin.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        """Return 401 JSON response instead of redirecting."""
        return jsonify({"error": "Unauthorized"}), 401

    # Register blueprints (you'll create these next)
    from app.routes import register_blueprints

    register_blueprints(app)

    # Serve frontend in production
    if os.getenv("FLASK_ENV") == "production":

        @app.route("/")
        def serve_frontend():
            """Serve the main frontend HTML file."""
            return send_from_directory(app.static_folder, "admin.html")

        @app.route("/<path:path>")
        def serve_static_files(path):
            """Serve static files (CSS, JS, etc.)."""
            # Don't serve API routes as static files
            if path.startswith("api/"):
                return {"error": "Not found"}, 404
            return send_from_directory(app.static_folder, path)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(e):
        return {"error": "Internal server error"}, 500

    return app
