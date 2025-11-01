import os
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Allow Render to set PORT; used by run.py if needed
    PORT = int(os.getenv('PORT', '5000'))


class DevelopmentConfig(Config):
    DEBUG = True
    # Local fallback DB for development if DATABASE_URL not provided
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'dev.db')


class ProductionConfig(Config):
    DEBUG = False
    # Render / Neon will provide DATABASE_URL (Postgres)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
