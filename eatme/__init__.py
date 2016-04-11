
"""
EatMe - calories tracking app
"""
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy

from .static_pages import static_pages

app = Flask(__name__, static_url_path='/static')

app.register_blueprint(static_pages)
