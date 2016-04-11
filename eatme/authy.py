from flask import g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from werkzeug.security import generate_password_hash, check_password_hash

basic_auth = HTTPBasicAuth()
multi_auth = MultiAuth(basic_auth)
auth = multi_auth

# Quick and dirty check during development
users = {
    "john": generate_password_hash("hello"),
    "susan": generate_password_hash("bye")
}

@basic_auth.verify_password
def verify_password(username, password):
    g.user = None
    if username in users:
        if check_password_hash(users.get(username), password):
            g.user = username
            return True
    return False
