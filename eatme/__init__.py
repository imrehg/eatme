
"""
EatMe - calories tracking app
"""
from flask import Flask, g, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

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

## Blueprints
from .api import api
from .static_pages import static_pages
app.register_blueprint(api)
app.register_blueprint(static_pages)

def init_db():
    # Create all databases
    db.create_all()

    # First setup, add administrator if does not exists
    from .models import User
    admin_account = User.query.filter_by(username='admin').first()
    if admin_account is None:
        admin = User('admin', '', app.config["ADMIN_PASSWORD_HASH"])
        db.session.add(admin)
        db.session.commit()