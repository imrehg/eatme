
"""
EatMe - calories tracking app
"""
from flask import Flask, send_from_directory
import os
app = Flask(__name__, static_url_path='/static')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/x-icon')

@app.route('/')
def home():
    return "Hello!"
