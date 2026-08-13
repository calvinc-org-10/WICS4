import os

# import app
import app_secrets
from sysver import sysver
from menuformname_viewMap4 import FormNameToURL_Map
from externalWebPageURL_Map4 import ExternalWebPageURL_Map

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
    DEV_MODE = app_secrets.sysver_key == 'DEV'
    APP_NAME = "WICS4"
    APP_VERSION = sysver[app_secrets.sysver_key]
    APP_LOGO_URL = '/assets/App-Logo.png'
    APP_NEWS_HTMLFILE = 'appNews.html'
    FORMNAME_TO_URL_MAP = FormNameToURL_Map
    EXTERNAL_WEBPAGE_URL_MAP = ExternalWebPageURL_Map
    STARTUP_URL = getattr(app_secrets, 'startup_URL', '/WICS')
    STARTUP_DELEGATE = getattr(app_secrets, 'startup_delegate', 'auth.login')
    
    MTLPHOTO_FOLDER = os.environ.get('MTLPHOTO_FOLDER') or getattr(app_secrets, 'MtlPhoto_folder', 'mtl_photos')
    MISC_FILELOC = getattr(app_secrets, 'MISC_FILELOC', os.getcwd())
    SAP_FILELOC = getattr(app_secrets, 'SAP_FILELOC', os.getcwd())

    ACCURACY_DANGER = 90        #	1	In Count Summary, Count Accuracy less than this value is highlighted red
    ACCURACY_SUCCESS = 98.5     #	1	In Count Summary, Count Accuracy higher than this value is highlighted green
    ACCURACY_WARNING = 95	    #1	In Count Summary, Count Accuracy at least this value (but less than ACCURACY-SUCCESS) is highlighted yellow
    COUNTLIST_RECLIMIT = 500
    LOCRPT_COUNTDAYS_IFNOSAP = 30

    DEFAULT_DATEFORMAT = '%Y-%m-%d'  # default date format for displaying dates in the app

    # this is a default value for new user password,
    # should be changed in production and moved to app_secrets.py or environment variable for better security
    NEWUSER_DEFAULT_PW = 'TempPassword123!'

    USER_AUTHENTICATION_ENABLED = getattr(app_secrets, 'usr_authentication_enabled', True)  # default to True if not specified in app_secrets
    # debugging - how to load calvincTools templates in subdirectories
    # EXPLAIN_TEMPLATE_LOADING = True


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        app_secrets.database_uri
        # f'sqlite:///{app_secrets.cMenu_dbPath}'
        # 'sqlite:///dev_database.db'
    SQLALCHEMY_ENGINE_OPTIONS = getattr(app_secrets, 'SQLALCHEMY_ENGINE_OPTIONS', {})
    # SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        app_secrets.database_uri
        # f'sqlite:///{app_secrets.cMenu_dbPath}'
        # 'sqlite:///prod_database.db'
    SQLALCHEMY_ENGINE_OPTIONS = getattr(app_secrets, 'SQLALCHEMY_ENGINE_OPTIONS', {})

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
