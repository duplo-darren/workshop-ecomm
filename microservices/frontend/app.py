from flask import Flask, jsonify
from .config import Config
from .routes import frontend_bp


def create_app():
    # static_folder=None: this service owns no static assets, and product images
    # under /static/uploads are proxied from the Catalog service instead.
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    app.register_blueprint(frontend_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"})

    return app
