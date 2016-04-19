import pyrfc3339
from datetime import datetime
from flask import Blueprint, g, jsonify, request
from flask.ext.security import auth_required, current_user
from flask.ext.security.utils import encrypt_password

from eatme import db, user_datastore
import eatme.models as models

from flask_inputs import Inputs
# from wtforms.validators import DataRequired, Email
from flask_inputs.validators import JsonSchema


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


api = Blueprint('api',
                __name__,
                template_folder='templates')


@api.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


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


@api.route('/api/v1/users', methods=['POST'])
def register_user():
    """
    Register new user. Requres ``email`` and ``password fields`` in POST data.

    **Example request**:

    .. sourcecode:: http

        POST /api/v1/users HTTP/1.1
        Host: example.com
        Accept: application/json

        {
            "email": "email@example.com",
            "password": "secret_password"
        }

    :status 200: When user successfully created
    :status 400: When input data is not validated
    :status 409: When an unser with such email address already exists
    """
    registration_inputs = RegistrationInputs(request)
    if not registration_inputs.validate():
        raise InvalidUsage(registration_inputs.errors, status_code=400)
        # return jsonify(success=False,)
    else:
        input = request.json
        if user_datastore.get_user(input['email']):
            raise InvalidUsage('user already exists', status_code=409)
        else:
            user = user_datastore.create_user(email=input['email'],
                                              password=encrypt_password(input['password']))
            if user:
                print("GOT NEW USER")
                db.session.commit()
        return jsonify(success=True)


@api.route('/api/v1/users/self/', defaults={'userid': None}, methods=['PUT'])
@api.route('/api/v1/users/<userid>', methods=['PUT'])
def manage_user(userid):
    """
    Modify user information

    :param userid:
    :return:
    """
    if request.method == 'PUT':
        form = UserForm(request.form)
        if form.validate():
            return jsonify(form)


@api.route('/api/v1/users/<userid>/records')
def users_records(userid):
    """
    Query user records

    :param userid:
    :return:
    """
    # TODO user records search
    return


"""
Records API
"""


@api.route('/api/v1/records', methods=['POST'])
@auth_required('token', 'session')
def add_record():
    """
    Create new record

    :return:
    """
    new_record_inputs = NewRecordInputs(request)
    if not new_record_inputs.validate():
        raise InvalidUsage(new_record_inputs.errors, status_code=400)
    else:
        input = request.json
        if input['userid'] != current_user.id and not current_user.has_role('editor'):
            raise InvalidUsage("No access to add records to this user.", status_code=403)

        user = user_datastore.get_user(input['userid'])
        if user is None:
            raise InvalidUsage("Invalid user", status_code=400)

        new_record = models.Record(user_id=input['userid'],
                                   calories=int(input['calories']),
                                   date_record=pyrfc3339.parse(input['date_record']),
                                   description=input['description'])
        db.session.add(new_record)
        db.session.commit()
        return models.record_schema.jsonify(new_record)


@api.route('/api/v1/records/<recordid>')
def records(recordid):
    """
    Query records

    :param recordid:
    :return:
    """
    # TODO records search
    return


"""
Data Schemas
"""
registration_schema = {
    "title": "A user registration object",
    "type": "object",
    "properties": {
        "email": {
            "type": "string",
            "format": "email"
        },
        "password": {
            "type": "string",
            "minLength": 1
        }
    },
    "required": ["email", "password"]
}


class RegistrationInputs(Inputs):
    json = [JsonSchema(schema=registration_schema)]


new_record_schema = {
    "title": "A new calories record",
    "type": "object",
    "properties": {
        "date_record": {
            "type": "string",
            "format": "date-time"
        },
        "description": {
            "type": "string",
            "maxlength": 10
        },
        "calories": {
            "type": "integer",
            "minimum": 0
        },
        "userid": {
            "type": "integer",
            "minimum": 1
        }
    },
    "required": ["date_record", "calories", "userid"]
}


class NewRecordInputs(Inputs):
    json = [JsonSchema(schema=new_record_schema)]
