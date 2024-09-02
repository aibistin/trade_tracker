import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("Sys Path: " + str(sys.path)   )
from flask import Flask
from dotenv import load_dotenv
from .extensions import db

load_dotenv('.flaskenv')
app = Flask(__name__)

# To share the Database Connection
if os.environ.get('FLASK_ENV') == 'testing':
    print("Created an In Memory Database")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    print("Created a File based Database")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../data/stock_trades.db'


# Initialize the db with the app
db.init_app(app)





from app import routes
