import os

import app
import app_secrets
from sysver import sysver
from menuformname_viewMap import FormNameToURL_Map
from externalWebPageURL_Map import ExternalWebPageURL_Map

class Config: 
    SECRET_KEY = os.environ.get('SECRET_KEY') or app_secrets.SECRET_KEY
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-WTF
    WTF_CSRF_ENABLED = True
    
    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600 * 24  # 24 hours

    # app specific
    APP_VERSION = sysver[app_secrets.sysver_key]
    APP_LOGO_URL = '/assets/App-Logo.png'
    APP_NEWS_HTMLFILE = 'appNews.html'
    FORMNAME_TO_URL_MAP = FormNameToURL_Map
    EXTERNAL_WEBPAGE_URL_MAP = ExternalWebPageURL_Map
    
    # this is a default value for new user password, 
    # should be changed in production and moved to app_secrets.py or environment variable for better security
    NEWUSER_DEFAULT_PW = 'TempPassword123!'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        app_secrets.database_uri
        # f'sqlite:///{app_secrets.cMenu_dbPath}'
        # 'sqlite:///dev_database.db'
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os. environ.get('DATABASE_URL') or \
        app_secrets.database_uri
        # f'sqlite:///{app_secrets.cMenu_dbPath}'
        # 'sqlite:///prod_database.db'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True  # HTTPS only


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
