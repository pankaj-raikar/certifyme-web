from flask import Flask, jsonify
from app.config import DevelopmentConfig
from app.extensions import db, migrate, login_manager, cors
from app.models import Admin


def create_app(config_class=DevelopmentConfig):
    """App factory — initialize Flask with extensions & blueprints."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cors.init_app(
        app,
        origins=["http://127.0.0.1:5500", "http://localhost:5500"],
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

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(e):
        return {"error": "Internal server error"}, 500

    return app
