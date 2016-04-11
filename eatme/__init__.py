
"""
EatMe - calories tracking app
"""
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__,
            instance_relative_config=True,
            static_url_path='/static')

## Blueprints
from .static_pages import static_pages
app.register_blueprint(static_pages)

## Configuration
# Load the default configuration
app.config.from_object('config.default')

# Load the configuration from the instance folder
app.config.from_pyfile('config.py', silent=True)

# Load the file specified by the APP_CONFIG_FILE environment variable
# Variables defined here will override those in the default configuration
app.config.from_envvar('APP_CONFIG_FILE', silent=True)
