import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os<｜begin▁of▁sentence｜>os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')