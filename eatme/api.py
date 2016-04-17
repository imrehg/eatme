from flask import Blueprint, g, jsonify
from flask.ext.security import auth_required

import eatme.models as models

api = Blueprint('api',
                __name__,
                template_folder='templates')

@api.route('/api/v1/users', defaults={'userid': None})
@api.route('/api/v1/users/<userid>')
@auth_required('token', 'session')
def users(userid):
    """Query users
    """
    if userid is not None:
        user = models.User.query.filter_by(id=userid).first()
        if user is not None:
            return models.user_schema.jsonify(user)
        else:
            # Should return "wrong ID"
            return {}
    else:
        users = models.User.query.all()
        if users is not None:
            result = models.users_schema.dump(users)
            return jsonify(users=result.data)
        else:
            # Should return "wrong ID"
            return {}

@api.route('/api/v1/passwd')
@auth_required('token', 'session')
def passwd():
    return "Hello!"

@api.route('/api/v1/login')
def login():
    return "Hello!"
