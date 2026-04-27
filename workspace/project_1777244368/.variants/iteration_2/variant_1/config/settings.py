from typing import Union
import os

class Config:
    """Base configuration class."""
    
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'this-really-needs-to-be-changed'
    @staticmethod
    def init_app(app):
        pass
    
class DevelopmentConfig(Config):
    """Development configuration class."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                               'sqlite:///' + os<｜begin▁of▁sentence｜>os.path.abspath(os.path.dirname(__file__)) + '/data-dev.sqlite'
    
class TestingConfig(Config):
    """Testing configuration class."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                               'sqlite:///' + os.path.abspath(os.path.dirname(__file__)) + '/data-test.sqlite'
    
class ProductionConfig(Config):
    """Production configuration class."""
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                               'sqlite:///' + os.path.abspath(os.path.dirname(__file__)) + '/data.sqlite'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
config: Union[DevelopmentConfig, TestingConfig, ProductionConfig] = DevelopmentConfig