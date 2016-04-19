import pyrfc3339
from datetime import datetime
from flask import Blueprint, g, jsonify, request
from flask.ext.security import auth_required, current_user
from flask.ext.security.utils import encrypt_password

from eatme import db, user_datastore
import eatme.models as models

from flask_inputs import Inputs
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


"""
User API
"""


@api.route('/api/v1/users', defaults={'userid': None})
@api.route('/api/v1/users/<int:userid>')
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


@api.route('/api/v1/users/<int:userid>/records', methods=['GET'])
@auth_required('token', 'session')
def users_records(userid):
    """
    Query user records

    :param userid:
    :return:
    """
    if userid != current_user.id and not current_user.has_role('editor'):
        raise InvalidUsage("No access to the records of this user.", status_code=403)

    user = models.User.query.filter_by(id=userid).first()
    if user is None:
        raise InvalidUsage("No such user.", status_code=400)

    # Apply filtering
    kwargs = {'user_id': userid}
    query = models.Record.query.filter_by(**kwargs)
    """ Progressive filtering on time """
    try:
        date_start = request.args.get('date_start')
        if date_start is not None:
            query_date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
            query = query.filter(models.Record.record_date >= query_date_start)
        date_end = request.args.get('date_end')
        if date_end is not None:
            query_date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
            query = query.filter(models.Record.record_date <= query_date_end)
        time_start = request.args.get('time_start')
        if time_start is not None:
            if len(time_start) < 6:
                time_start += ':00'
            query_time_start = datetime.strptime(time_start, '%H:%M:%S').time()
            query = query.filter(models.Record.record_time >= query_time_start)
        time_end = request.args.get('time_end')
        if time_end is not None:
            if len(time_end) < 6:
                time_end += ':00'
            query_time_end = datetime.strptime(time_end, '%H:%M:%S').time()
            query = query.filter(models.Record.record_time <= query_time_end)
    except ValueError:
        raise InvalidUsage("Invalid query parameters.", status_code=400)

    current_records = query.all()
    result = models.records_schema.dump(current_records)
    return jsonify(records=result.data)


@api.route('/api/v1/users/<int:userid>/targets', methods=['GET', 'PUT'])
@auth_required('token', 'session')
def users_targets(userid):
    """
    Query user targets

    :param userid:
    :return:
    """
    if userid != current_user.id and not current_user.has_role('editor'):
        raise InvalidUsage("No access to the records of this user.", status_code=403)

    user = models.User.query.filter_by(id=userid).first()
    if user is None:
        raise InvalidUsage("No such user.", status_code=400)

    if request.method == 'GET':
        result = models.target_schema.dump(user)
        return jsonify(targets=result.data)
    elif request.method == 'PUT':
        target_inputs = TargetInputs(request)
        if not target_inputs.validate():
            raise InvalidUsage(target_inputs.errors, status_code=400)
        target_json = request.json
        user.target_daily_calories = int(target_json['target_daily_calories'])
        db.session.commit()
        return jsonify(success=True, settings=target_json)
    else:
        raise InvalidUsage("Method not allowed (only GET and PUT)", status_code=405)


@api.route('/api/v1/users/<int:userid>/roles', methods=['GET', 'PUT', 'DELETE'])
@auth_required('token', 'session')
def users_roles(userid):
    """
    Query user targets

    :param userid:
    :return:
    """
    if not current_user.has_role('admin'):
        raise InvalidUsage("Only administrators have access to user roles.", status_code=403)

    user = models.User.query.filter_by(id=userid).first()
    if user is None:
        raise InvalidUsage("No such user.", status_code=400)

    possible_roles = ['admin', 'editor']

    if request.method == 'GET':
        this_user_roles = []
        for role in possible_roles:
            if user.has_role(role):
                this_user_roles += [role]
        return jsonify(roles=this_user_roles)
    elif request.method == 'PUT':
        role_input = RoleInputs(request)
        if not role_input.validate():
            raise InvalidUsage(role_input.errors, status_code=400)
        role_json = request.json
        role = user_datastore.find_role(role_json['role'])
        if role is None:
            raise InvalidUsage("No applicable role found", status_code=400)
        user_datastore.add_role_to_user(user, role)
        db.session.commit()
        return jsonify(success=True, settings=role_json)
    elif request.method == 'DELETE':
        role_input = RoleInputs(request)
        if not role_input.validate():
            raise InvalidUsage(role_input.errors, status_code=400)
        role_json = request.json
        role = user_datastore.find_role(role_json['role'])
        if role is None:
            raise InvalidUsage("No applicable role found", status_code=400)
        user_datastore.remove_role_from_user(user, role)
        db.session.commit()
        return jsonify(success=True, settings=role_json)
    else:
        raise InvalidUsage("Method not allowed (only GET/PUT/DELETE)", status_code=405)


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

        try:
            record_date = datetime.strptime(input['record_date'], '%Y-%m-%d').date()
        except ValueError:
            raise InvalidUsage("Invalid date given", status_code=400)

        try:
            if len(input['record_time']) > 5:
                """ Use full time format: 12:30:45 """
                record_time = datetime.strptime(input['record_time'], '%H:%M:%S').time()
            else:
                """ Use hour/minute time format: 12:30 """
                record_time = datetime.strptime(input['record_time'], '%H:%M').time()
        except ValueError:
            raise InvalidUsage("Invalid time given", status_code=400)

        new_record = models.Record(user_id=input['userid'],
                                   calories=int(input['calories']),
                                   record_date=record_date,
                                   record_time=record_time,
                                   description=input['description'])
        db.session.add(new_record)
        db.session.commit()
        return models.record_schema.jsonify(new_record)


@api.route('/api/v1/records/<int:recordid>', methods=['GET', 'PUT', 'DELETE'])
@auth_required('token', 'session')
def records(recordid):
    """
    Query records

    :param recordid:
    :return:
    """
    record = models.Record.query.filter_by(id=recordid).first()
    if record is None:
        raise InvalidUsage("No such record.", status_code=400)

    if record.user_id != current_user.id and not current_user.has_role('editor'):
        raise InvalidUsage("No access to the records of this user.", status_code=403)

    if request.method == 'GET':
        result = models.record_schema.dump(record)
        return jsonify(targets=result.data)
    elif request.method == 'PUT':
        updated_records_inputs = UpdatedRecordInputs(request)
        if not updated_records_inputs.validate():
            raise InvalidUsage(updated_records_inputs.errors, status_code=400)
        update_json = request.json
        if 'calories' in update_json:
            record.calories = int(update_json['calories'])
        if 'record_date' in update_json:
            try:
                record_date = datetime.strptime(update_json['record_date'], '%Y-%m-%d').date()
            except ValueError:
                raise InvalidUsage("Invalid date given", status_code=400)
            record.record_date = record_date

        if 'record_time' in update_json:
            try:
                if len(update_json['record_time']) > 5:
                    """ Use full time format: 12:30:45 """
                    record_time = datetime.strptime(update_json['record_time'], '%H:%M:%S').time()
                else:
                    """ Use hour/minute time format: 12:30 """
                    record_time = datetime.strptime(update_json['record_time'], '%H:%M').time()
            except ValueError:
                raise InvalidUsage("Invalid time given", status_code=400)
            record.record_time = record_time

        if 'description' in update_json:
            record.description = update_json['description']

        db.session.commit()
        return models.record_schema.jsonify(record)
    elif request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        return jsonify(success=True)
    else:
        raise InvalidUsage("Method not allowed (only GET and PUT)", status_code=405)


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
        "record_date": {
            "type": "string",
        },
        "record_time": {
            "type": "string",
        },
        "description": {
            "type": "string",
            "maxlength": 255
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
    "required": ["record_date", "record_time", "calories", "userid"]
}


class NewRecordInputs(Inputs):
    json = [JsonSchema(schema=new_record_schema)]


updated_record_schema = {
    "title": "An updated calories record",
    "type": "object",
    "properties": {
        "record_date": {
            "type": "string",
        },
        "record_time": {
            "type": "string",
        },
        "description": {
            "type": "string",
            "maxlength": 255
        },
        "calories": {
            "type": "integer",
            "minimum": 0
        },
    },
}


class UpdatedRecordInputs(Inputs):
    json = [JsonSchema(schema=updated_record_schema)]


target_schema = {
    "title": "A user registration object",
    "type": "object",
    "properties": {
        "target_daily_calories": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100000
        },
    },
    "required": ["target_daily_calories"]
}


class TargetInputs(Inputs):
    json = [JsonSchema(schema=target_schema)]


roles_schema = {
    "title": "A user roles object",
    "type": "object",
    "properties": {
        "role": {
            "enum": ["admin", "editor"]
        },
    },
    "required": ["role"]
}


class RoleInputs(Inputs):
    json = [JsonSchema(schema=roles_schema)]
