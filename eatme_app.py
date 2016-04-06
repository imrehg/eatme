"""
EatMe - calories tracking app
"""
from flask import Flask
import os

app = Flask(__name__)

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
