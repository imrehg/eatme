
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

if __name__ == '__main__':
    # Run in stand-alone environment
    try:
        PORT = int(os.environ['PORT'])
    except KeyError:
        PORT = 5000
    app.run(host='127.0.0.1', port=PORT, debug=True)
