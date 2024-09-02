import sys
import os
# from config import Config
# Add the project root directory to  the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask
from dotenv import load_dotenv
load_dotenv('.flaskenv')  # Load environment variables from .flaskenv

app = Flask(__name__)
# app.config.from_object(Config)
from app import routes
