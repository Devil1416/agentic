from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask app
app = Flask(__name__)

# Configure database URI and secret key
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os<｜begin▁of▁sentence｜>os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

# Initialize SQLAlchemy
db = SQLAlchemy(app)