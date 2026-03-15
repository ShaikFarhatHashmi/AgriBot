import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    from settings import AppConfig
    app.config.from_object(AppConfig)
    app.config["APP_CONFIG"] = AppConfig

    from .routes.chat_routes  import chat_bp
    from .routes.auth_routes  import auth_bp
    from .routes.image_routes import image_bp
    from .routes.history_routes import history_bp
    from .routes.qr_routes import qr_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(auth_bp,    url_prefix="/auth")
    app.register_blueprint(image_bp,   url_prefix="/image")
    app.register_blueprint(history_bp)
    app.register_blueprint(qr_bp, url_prefix="/qr")

    # ── Initialise chat history DB ────────────────────────────
    # Creates chat_history.db and tables on first run.
    # Safe to call every startup — uses IF NOT EXISTS.
    from app.models.chat_history import init_db
    init_db()

    # ── QA Service Note ───────────────────────────────────────
    # QA Service will initialize on first use (takes 2-5 minutes)
    # This prevents app startup from hanging
    print("[AgriBot] QA Service will initialize on first question (2-5 minutes)")
    print("[AgriBot] App is ready! Open browser and ask a question.")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app