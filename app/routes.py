import os
from app import app
from app.utils import SYMBOLS_TO_EXCLUDE

print(f"[routes.py] Flask Env = {os.environ.get('FLASK_ENV')}")

if __name__ == "__main__":
    app.run(debug=True)


# from sqlalchemy import select
# from flask import Blueprint, Flask, render_template, request
# from .extensions import db
# from app import app
# from .routes import web_routes, api_routes
# from .models.models import (
#     Security,
# )

# Create blueprints
# web_bp = Blueprint("web", __name__)
# api_bp = Blueprint("api", __name__, url_prefix="/api")
# Register blueprints
# app.register_blueprint(web_bp)
# app.register_blueprint(api_bp)
# Import route definitions
from .routes.web_routes import *
from .routes.api_routes import *

# print(f"[routes.py] Flask Env = {os.environ.get('FLASK_ENV')}")

# app = Flask(__name__)
print("[routes.py] Inside Routes name: " + __name__)

# Create the database tables (only needed once)
with app.app_context():
    db.create_all()

@app.before_request
def before_request():
    print(f"[routes.py] Before request: {request.method} {request.url}")


if __name__ == "__main__":
    app.run(debug=True)  # Run the Flask app in debug mode
