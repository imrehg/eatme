from flask import Blueprint, abort, render_template, send_from_directory
from jinja2 import TemplateNotFound
import os

static_pages = Blueprint('static_pages',
                         __name__,
                         template_folder='templates')

@static_pages.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(static_pages.root_path, 'static'),
                               'favicon.ico', mimetype='image/x-icon')

@static_pages.route('/')
def home():
    return "Hello!"
