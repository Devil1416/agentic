import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config(object):
    """Base configuration class. Uses environment variables."""
    
    SECRET_KEY = os.getenv('SECRET_KEY') or 'default-secret-key'
    SQLALCHEMY_DATABASE_URI = os<｜begin▁of▁sentence｜>os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')