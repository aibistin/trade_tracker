# tests/helpers.py
"""Shared test utilities."""
import os

from app import create_app
from app.extensions import db


def create_test_app(flask_env="dev"):
    """App factory for tests — always uses an in-memory database.

    flask_env: "dev" (default) bypasses the API key check; pass None to leave
    FLASK_ENV unset so API auth enforcement itself can be tested.

    The in-memory URI must be passed INTO create_app (as test_config) —
    assigning app.config["SQLALCHEMY_DATABASE_URI"] after create_app returns
    is silently ignored because the engine is already bound, and tests would
    read and write the real data/stock_trades.db.
    """
    if flask_env is None:
        os.environ.pop("FLASK_ENV", None)
    else:
        os.environ["FLASK_ENV"] = flask_env

    app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    # Regression guard: fail loudly if the app is bound to a file database
    with app.app_context():
        engine_url = str(db.engine.url)
        assert engine_url == "sqlite:///:memory:", (
            f"Tests must run against an in-memory database, got: {engine_url}"
        )
    return app
