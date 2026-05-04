def register_blueprints(app):
    """Register all route blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.opportunities import opportunities_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(opportunities_bp)
