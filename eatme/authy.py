from flask import g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from werkzeug.security import generate_password_hash
from eatme.models import User

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
    if username is None or password is None:
        return False
    g.user = None
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
            g.user = username
            return True
    return False


def genpass(password):
    return generate_password_hash(password)