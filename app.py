from flask import Flask, app, render_template, request, redirect, url_for, session
from flask_migrate import Migrate

from calvincTools.config import calvincTools_config
from calvincTools import calvincTools_init

# from database import app_db
# from app_secrets import *   # pylint: disable=wildcard-import
import app_secrets
import config

def create_app(config_name=app_secrets.config_to_use):  # type: ignore
    flskapp = Flask(__name__, static_folder='assets', template_folder='templates')
    flskapp.config.from_object(config.config[config_name])
    flskapp.config.from_mapping(calvincTools_config)
    # This is where you can add any additional configuration settings specific to your application
    flskapp.config['SQLALCHEMY_BINDS']['cToolsdb'] = app_secrets.cTools_BIND

    # the default calvincTools_config is simply:
    # calvincTools_config = {
    #     'SQLALCHEMY_BINDS': {'cToolsdb': app_secrets.cTools_BIND},
    # if you want store the cTools database in a different location (I STRONGLY recommend that), you can override the default by adding a new entry to your config file like this:
    #     'SQLALCHEMY_BINDS': {'cToolsdb': 'sqlite:///path/to/your/cTools.db'}, }
    # you don't have to name the bind_key 'cToolsdb', but if you do, you need to pass that name 
    # to the init_cDatabase function like this: 
    #       init_cDatabase(app, app_db, cTools_bind_key='myBindKey')
    # if you don't specify a bind_key, it will default to 'cToolsdb', so if you want to use the default, you don't have to do anything else.

    # Finallly, if the cTools tables in your database have different names than the default, you can specify those as well by passing them as arguments to the init_cDatabase function like this:
    #       table_names_dict = {
    #           'menuGroups': 'cMenu_menuGroups',
    #           'menuItems': 'cMenu_menuItems',
    #           'cParameters': 'cMenu_cParameters',
    #           'cGreetings': 'cMenu_cGreetings',
    #           'User': 'users',
    #           }
    #       init_cDatabase(app, app_db, cTools_bind_key='myBindKey', cTools_table_names=table_names_dict)
    # the names in the above example are the default names, 
    # so if the table names in your database are the same as the default (or you're OK with calvincTools creating them), 
    # you don't have to specify them.
    
    # sorry, there's no way of changing the field names in the cTools tables. Too much of the calvincTools code relies on those field names
    
    # These settings should be made before callvinc calvincTools_init()
    
    # Initialize extensions
    from database import app_db
    app_db.init_app(flskapp)
    # migrate = Migrate(flskapp, cMenu_db)

    from models import cTools_tablenames, cTools_models  # import the cTools models to ensure they are registered with calvincTools before we initialize it. This is necessary for calvincTools to be able to create the tables in the database if they don't already exist. The cTools_models dict is populated in models.py when the cTools models are defined, so we just need to import it here to ensure that the models are registered with calvincTools before we initialize it.
    from sqlalchemy.orm import relationship
    # initialize calvincTools extensions
    (menuGroups, menuItems, cParameters, cGreetings, User) = calvincTools_init(
        flskapp, 
        app_db, 
        cTools_tablenames=cTools_tablenames, 
        cTools_models=cTools_models
        ).cTools_tables

    # define routes
    @flskapp.route('/')       # I don't want / to be valid
    def app_homepage():
        """Home page route."""
        return render_template('errors/404.html'), 404

    @flskapp.route(app_secrets.startup_URL)
    def startup():
        """Startup page route."""
        return redirect(url_for('auth.login'))  # Redirect to the login page

    # quite optional    
    @flskapp.route('/about')
    def about():
        """About page route."""
        return render_template('about.html')

    return flskapp


app = create_app()
if __name__ == '__main__':
    app.run(debug=True)

