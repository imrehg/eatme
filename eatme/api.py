from flask import Blueprint, g, jsonify

from .authy import auth

api = Blueprint('api',
                __name__,
                template_folder='templates')

@api.route('/api/v1/users', defaults={'userid': None})
@api.route('/api/v1/users/<userid>')
@auth.login_required
def users(userid):
    """Query users
    """
    return "Userid: {}".format(userid)
