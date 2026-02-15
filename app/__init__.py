import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import json_log_formatter
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
from .extensions import db

load_dotenv(".flaskenv")


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

    logs_dir = os.path.join(app.root_path, "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Configure logging
    # log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))   
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # File handler (rotating logs)
    file_handler = RotatingFileHandler(
        filename=os.path.join(logs_dir, "trading_app.log"),
        maxBytes=2 * 1024 * 1024,  # 2MB
        backupCount=5,
    )

    if os.environ.get('JSON_LOGGING','N') == 'Y':
        file_handler.setFormatter(json_log_formatter.JSONFormatter())   
    else:
        file_handler.setFormatter(logging.Formatter(log_format))

    file_handler.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    console_handler.setLevel(log_level)

    if os.environ.get("FLASK_ENV") == "production":
        # Only log WARNING and above to console
        console_handler.setLevel(logging.WARNING)
        #     Log DEBUG and above to file
        file_handler.setLevel(logging.DEBUG)

    # Configure Flask's logger
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    app.logger.propagate = False

    # Configure root logger for lib/ modules
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level)

    # Middleware for request logging
    @app.before_request
    def log_request_info():
        app.logger.info(
            f"Request: {request.method} {request.path} - Client: {request.remote_addr}"
        )
        if request.method in ["POST", "PUT"]:
            app.logger.debug(f"Request body: {request.get_data(as_text=True)}")

    @app.after_request
    def log_response_info(response):
        app.logger.info(
            f"Response: {response.status} - {request.method} {request.path}"
        )
        return response


    # Instead of app.logger.info(...)
    logger = logging.getLogger(__name__)

    logger.info(f"[__init__.py] Log Level: {log_level}")

    # Database configuration
    if os.environ.get("FLASK_ENV") == "testing":
        logger.debug("[__init__.py] Created an In Memory Database")
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        app.logger.debug("[__init__.py] Created a File based Database")
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../data/stock_trades.db"

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from .routes.web_routes import web_bp
    from .routes.api_routes import api_bp
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create database tables
    with app.app_context():
        db.create_all()
        app.logger.info("[__init__.py] Database tables created")

    return app


# Create app instance
app = create_app()
app.logger.info("[__init__.py] Application instance created")
