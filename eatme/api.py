from flask import Blueprint, g, jsonify

from . import ma
from .authy import auth
import eatme.models as models

api = Blueprint('api',
                __name__,
                template_folder='templates')

@api.route('/api/v1/users', defaults={'userid': None})
@api.route('/api/v1/users/<userid>')
@auth.login_required
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
