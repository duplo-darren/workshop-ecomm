from flask import Flask, jsonify
from .config import Config
from .models import db
from .routes import inventory_bp


# Advisory lock guarding schema creation. Distinct per service so the two never
# wait on each other.
SCHEMA_LOCK_ID = 0x1EC00002


def create_schema():
    """Create any missing tables, serialised across workers and replicas.

    Every Gunicorn worker in every replica runs this at boot. Against an empty
    database an unsynchronised CREATE TABLE races: all but one lose with a
    duplicate-key error on pg_type and that worker dies. Taking a
    transaction-scoped advisory lock first makes the check-and-create atomic, so
    the losers simply find the tables already present and carry on.
    """
    with db.engine.begin() as conn:
        conn.execute(db.text("SELECT pg_advisory_xact_lock(:id)"), {"id": SCHEMA_LOCK_ID})
        db.metadata.create_all(bind=conn)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(inventory_bp, url_prefix="/api")

    @app.route("/health")
    def health():
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "healthy"})

    with app.app_context():
        create_schema()

    return app
