"""
EatMe - calories tracking app
"""
from flask import Flask, g, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask_mail import Mail

app = Flask(__name__,
            instance_relative_config=True,
            static_url_path='/static')

## Configuration
# Load the default configuration
app.config.from_object('config.default')

# Load the configuration from the instance folder
app.config.from_pyfile('config.py', silent=True)

# Load the file specified by the APP_CONFIG_FILE environment variable
# Variables defined here will override those in the default configuration
app.config.from_envvar('APP_CONFIG_FILE', silent=True)

app.config['SQLALCHEMY_DATABASE_URI'] = app.config["DATABASE_URI"]
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Setup Flask-Security
from .models import User, Role

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

## Blueprints
from .api import api
from .static_pages import static_pages

app.register_blueprint(api)
app.register_blueprint(static_pages)

# Add mail service
# See: https://pythonhosted.org/Flask-Security/quickstart.html#id4
if app.config['MAIL']:
    mail = Mail(app)


# Create a user to test with
@app.before_first_request
def create_user():
    """
    Create admin default account on first request if does not exists.
    """
    db.create_all()
    admin_email = app.config["ADMIN_EMAIL"]
    admin = user_datastore.get_user(admin_email)
    if admin is None:
        user_datastore.create_user(email=admin_email, password=app.config["ADMIN_PASSWORD_HASH"])
        db.session.commit()
