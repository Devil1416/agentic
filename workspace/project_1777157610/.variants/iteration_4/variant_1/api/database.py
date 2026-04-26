from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL') or 'sqlite:///./test.db'
# SQLAlchemy engine, which is the core component of any SQLAlchemy application and represents a pool of connections to your database.
engine = create_engine(SQLALCHEMY_DATABASE_URL) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# The declarative base class is the superclass for all models and contains a MetaData collection that keeps together all the different information.
Base = declarative_base()