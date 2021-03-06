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
        if 'meta' not in rv:
            rv['meta'] = {}
        rv['meta'] = {'code': self.status_code}
        if 'response' not in rv:
            rv['response'] = {}
        if 'error' not in rv['response']:
            rv['response']['error'] = {}
        rv['response']['error']['message'] = self.message
        return rv


def wrap200code(**kwargs):
    response_object = {}
    for key, value in kwargs.items():
        response_object[key] = value
    rv = {'meta': {'code': 200},
          'response': response_object}
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
    """Query users.

    If ``userid`` is given, then query the specific user, while without ``userid``
    the whole dataset is queried.

    Only users with ``admin`` or ``editor`` roles can query other users or the whole list.

    **Example request:**

    .. sourcecode:: http

        GET /api/v1/users/2 HTTP/1.0
        Authorization: TOKEN
        Accept: application/json

    **Corresponding response:**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 489
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 14:28:58 GMT

        {
            "meta": {
                "code": 200
            },
            "response": {
                "user": {
                    "_links": {
                        "collection": "/api/v1/users",
                        "records": "/api/v1/users/2/records",
                        "roles": "/api/v1/users/2/roles",
                        "self": "/api/v1/users/2",
                        "targets": "/api/v1/users/2/targets"
                    },
                    "date_created": "2016-04-19T05:39:11+00:00",
                    "date_modified": "2016-04-19T14:17:21+00:00",
                    "email": "xyz@a.com",
                    "id": 2,
                    "target_daily_calories": 0
                }
            }
        }

    :qparam auth_token: Optional token for authentication if no :http:header:`Authorization` nor session cookie is sent.

    :reqheader Authorization: Optional token for authentication if no ``auth_token`` nor session cookie is sent.

    :status 200: A correct query with proper authorization
    :status 400: If a wrong user ID is queried.
    :status 403: If the current user does not have permission to do the particular query
    """
    if userid is not None:
        if userid == current_user.id or current_user.has_role('editor') or current_user.has_role('editor'):
            user = models.User.query.filter_by(id=userid).first()
            if user is not None:
                result = models.user_schema.dump(user)
                return jsonify(wrap200code(user=result.data))
            else:
                raise InvalidUsage('Wrong user id.', status_code=400)
        else:
            raise InvalidUsage("No access to query this user.", status_code=403)
    else:
        if current_user.has_role('admin') or current_user.has_role('editor'):
            users = models.User.query.all()
            if users is not None:
                result = models.users_schema.dump(users)
                return jsonify(wrap200code(users=result.data))
            else:
                # This should never happen
                raise jsonify(wrap200code(users=[]))
        else:
            raise InvalidUsage("No access to query all users.", status_code=403)


@api.route('/api/v1/users/self')
@auth_required('token', 'session')
def user_self():
    """Getting the current use user's data

    **Example request:**

    .. sourcecode:: http

        GET /api/v1/users/self HTTP/1.0
        Authorization: TOKEN

    **Example response:**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 489
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:04:18 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "user": {
              "_links": {
                "collection": "/api/v1/users",
                "records": "/api/v1/users/2/records",
                "roles": "/api/v1/users/2/roles",
                "self": "/api/v1/users/2",
                "targets": "/api/v1/users/2/targets"
              },
              "date_created": "2016-04-19T05:39:11+00:00",
              "date_modified": "2016-04-19T14:17:21+00:00",
              "email": "xyz@a.com",
              "id": 2,
              "target_daily_calories": 0
            }
          }
        }

    :qparam auth_token: Optional token for authentication if no :http:header:`Authorization` nor session cookie is sent.

    :reqheader Authorization: Optional token for authentication if no ``auth_token`` nor session cookie is sent.

    :status 200: Successful query
    :status 401: If not authenticated (not logged in)
    """
    return users(current_user.id)


@api.route('/api/v1/users', methods=['POST'])
def register_user():
    """
    Register new user. Requires ``email`` and ``password`` fields.

    **Example request**:

    .. sourcecode:: http

        POST /api/v1/users HTTP/1.0
        Host: example.com
        Accept: application/json

        {
            "email": "email@example.com",
            "password": "secret_password"
        }

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 76
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:42:48 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "success": true
          }
        }

    :status 200: When user successfully created
    :status 400: When input data is not validated
    :status 409: When an user with such email address already exists
    """
    registration_inputs = RegistrationInputs(request)
    if not registration_inputs.validate():
        raise InvalidUsage(registration_inputs.errors, status_code=400)
    else:
        input = request.json
        if user_datastore.get_user(input['email']):
            raise InvalidUsage('user already exists', status_code=409)
        else:
            user = user_datastore.create_user(email=input['email'],
                                              password=encrypt_password(input['password']))
            if user:
                db.session.commit()
        return jsonify(wrap200code(success=True))


@api.route('/api/v1/users/self', defaults={'userid': None}, methods=['PUT'])
@api.route('/api/v1/users/<userid>', methods=['PUT'])
def manage_user(userid):
    """Modify user information

    :param userid: the ID of user to be modified
    :status 501: User modifications are not implemented yet
    """
    # Todo: impelemnt user functions
    raise InvalidUsage('User modifications not implemented yet', status_code=501)


@api.route('/api/v1/users/<int:userid>/records', methods=['GET'])
@auth_required('token', 'session')
def users_records(userid):
    """
    Query records of a specific user.

    .. sourcecode:: http

        GET /api/v1/users/2/records HTTP/1.0
        Authorization: TOKEN
        Accept: application/jsoHTTP/1.0

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 960
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 14:44:12 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "records": [
              {
                "calories": 150,
                "date_created": "2016-04-19T05:43:02+00:00",
                "date_modified": "2016-04-19T05:49:03+00:00",
                "description": "Sandwich",
                "id": 2,
                "record_date": "2016-04-19",
                "record_time": "19:15:00",
                "user_id": 2
              },
              {
                "calories": 120,
                "date_created": "2016-04-19T05:41:17+00:00",
                "date_modified": "2016-04-19T05:41:17+00:00",
                "description": "Sandwich",
                "id": 1,
                "record_date": "2016-04-12",
                "record_time": "12:30:00",
                "user_id": 2
              }
            ]
          }
        }

    :param userid: Which user's records to query. If not the current user's, then need to have ``editor`` role.
    :qparam date_start: Date to query equal or after, in RFC 3339 format: 'YYYY-MM-DD', eg. ``2016-04-19``
    :qparam date_end: Date to query equal or before, in RFC 3339 format: 'YYYY-MM-DD', eg. ``2016-04-19``
    :qparam time_start: Time each day to query equal or after, in 'HH:MM' or 'HH:MM:SS' format (24H), eg. ``21:30`` or ``21:30:21``
    :qparam time_end: Time each day to query equal or before, in 'HH:MM' or 'HH:MM:SS' format (24H), eg. ``21:30`` or ``21:30:21``
    :qparam auth_token: Optional token for authentication if no :http:header:`Authorization` nor session cookie is sent.

    :reqheader Authorization: Optional token for authentication if no ``auth_token`` nor session cookie is sent.
    :status 200: If query successful.
    :status 400: If no such user exists.
    :status 403: If not authorized to query that particular user.
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

    current_records = query.order_by(models.Record.record_date.desc(), models.Record.record_time.desc()).all()
    result = models.records_schema.dump(current_records)
    return jsonify(wrap200code(records=result.data))


@api.route('/api/v1/users/<int:userid>/targets', methods=['GET', 'PUT'])
@auth_required('token', 'session')
def users_targets(userid):
    """Query or update user targets, such as daily calories goals.

    **Example query request:**

    .. sourcecode:: http

        GET /api/v1/users/2/targets HTTP/1.0
        Authorization: TOKEN

    **Example query response:**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 127
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:09:46 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "targets": {
              "id": 2,
              "target_daily_calories": 1200
            }
          }
        }

    **Example update request:**

    .. sourcecode:: http

        PUT /api/v1/users/2/targets HTTP/1.0
        Authorization: TOKEN

        {
            "target_daily_calories": 1100
        }

    **Example update response:**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 116
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:16:42 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "settings": {
              "target_daily_calories": 1100
            }
          }
        }

    :qparam auth_token: Optional token for authentication if no :http:header:`Authorization` nor session cookie is sent.

    :reqheader Authorization: Optional token for authentication if no ``auth_token`` nor session cookie is sent.

    :param userid: the id of user being queried or modified. For modifying a different user than the one logged in needs ``editor`` rote.
    :status 200: Successful query
    :status 400: If no user exists who correspond to the one queried
    :status 401: If not authenticated (not logged in)
    :status 403: If not authorized
    """
    if userid != current_user.id and not current_user.has_role('editor'):
        raise InvalidUsage("No access to the records of this user.", status_code=403)

    user = models.User.query.filter_by(id=userid).first()
    if user is None:
        raise InvalidUsage("No such user.", status_code=400)

    if request.method == 'GET':
        result = models.target_schema.dump(user)
        return jsonify(wrap200code(targets=result.data))
    elif request.method == 'PUT':
        target_inputs = TargetInputs(request)
        if not target_inputs.validate():
            raise InvalidUsage(target_inputs.errors, status_code=400)
        target_json = request.json
        user.target_daily_calories = int(target_json['target_daily_calories'])
        db.session.commit()
        return jsonify(wrap200code(settings=target_json))
    else:
        raise InvalidUsage("Method not allowed (only GET and PUT)", status_code=405)


@api.route('/api/v1/users/<int:userid>/roles', methods=['GET', 'PUT', 'DELETE'])
@auth_required('token', 'session')
def users_roles(userid):
    """Query and update user roles

    Available roles: ``admin`` and ``editor``.

    ``admin``: can change roles for other users, can query user list.
    ``editor``: can query and change records for all user

    **Example query request:**

    .. sourcecode:: http

        GET /api/v1/users/1/roles HTTP/1.0
        Authorization: TOKEN

    **Example query result:**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 107
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:22:05 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "roles": [
              "admin",
              "editor"
            ]
          }
        }

    **Example request to add role:**

    .. sourcecode:: http

        PUT /api/v1/users/2/roles HTTP/1.0
        Authorization: TOKEN

        {
            "role": "editor"
        }

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 103
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:26:04 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "settings": {
              "role": "editor"
            }
          }
        }

    **Example request to remove role:**

    .. sourcecode:: http

        DELETE /api/v1/users/2/roles HTTP/1.0
        Authorization: TOKEN

        {
            "role": "editor"
        }

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 103
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:27:30 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "settings": {
              "role": "editor"
            }
          }
        }

    :qparam auth_token: Optional token for authentication if no :http:header:`Authorization` nor session cookie is sent.

    :reqheader Authorization: Optional token for authentication if no ``auth_token`` nor session cookie is sent.

    :param userid: the id of user being queried or modified. For modifying a different user than the one logged in needs ``editor`` rote.
    :status 200: Successful query
    :status 400: If no user exists who correspond to the one queried, or no applicable role found
    :status 401: If not authenticated (not logged in)
    :status 403: If not authorized
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
        return jsonify(wrap200code(roles=this_user_roles))
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
        return jsonify(wrap200code(settings=role_json))
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
        return jsonify(wrap200code(settings=role_json))
    else:
        raise InvalidUsage("Method not allowed (only GET/PUT/DELETE)", status_code=405)


"""
Records API
"""


@api.route('/api/v1/records', methods=['POST'])
@auth_required('token', 'session')
def add_record():
    """Create new record

    **Example new record query:**

    .. sourcecode:: http

        POST /api/v1/records HTTP/1.0
        Authorization: TOKEN

        {
            "record_date": "2016-04-12",
            "record_time": "12:30",
            "calories": 120,
            "description": "Sandwich",
            "userid": 2
        }

    **Example new record response:**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 344
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:47:49 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "new_record": {
              "calories": 120,
              "date_created": "2016-04-19T15:47:49+00:00",
              "date_modified": "2016-04-19T15:47:49+00:00",
              "description": "Sandwich",
              "id": 17,
              "record_date": "2016-04-12",
              "record_time": "12:30:00",
              "user_id": 2
            }
          }
        }

    :qparam record_date: Date associated with the record, in "YYYY-MM-DD" format, e.g. ``2016-04-19``.
    :qparam record_time: Time association with the record, in 24h format, either "%H:%M" or "%H:%M:%S", eg. ``12:30`` or ``12:30:15``.
    :qparam calories: Calories (in integers).
    :qparam description: An optional description of the record.
    :qparam userid: An existing user ID.
    :qparam auth_token: Optional token for authentication if no :http:header:`Authorization` nor session cookie is sent.

    :reqheader Authorization: Optional token for authentication if no ``auth_token`` nor session cookie is sent.

    :status 200: If record successfully added
    :status 400: If invalid data is posted
    :status 403: If does not have authorization to create data for the specific user
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
        results = models.record_schema.dump(new_record)
        return jsonify(wrap200code(new_record=results.data))


@api.route('/api/v1/records/<int:recordid>', methods=['GET', 'PUT', 'DELETE'])
@auth_required('token', 'session')
def records(recordid):
    """Query and modify records

    **Modification:**

    Submit only the parameteres that need to be modified (``record_date``, ``record_time``, ``description``, ``calories``).
    The ``user_id`` cannot be modified!

    **Example request to modify record:**

    .. sourcecode:: http

        PUT /api/v1/records/17 HTTP/1.0
        Authorization: TOKEN

        {
            "record_date": "2016-04-19",
            "record_time": "19:15",
            "calories": 150
        }

    **Example response to modify record:**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 340
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 16:02:23 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "record": {
              "calories": 150,
              "date_created": "2016-04-19T15:47:49+00:00",
              "date_modified": "2016-04-19T16:02:05+00:00",
              "description": "Sandwich",
              "id": 17,
              "record_date": "2016-04-19",
              "record_time": "19:15:00",
              "user_id": 2
            }
          }
        }


    **Example request to remove a record:**

    .. sourcecode:: http

        DELETE /api/v1/records/5 HTTP/1.0
        Authorization: TOKEN

    **Example response to remove a record:**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 76
        Server: Werkzeug/0.11.8 Python/3.5.1
        Date: Tue, 19 Apr 2016 15:59:35 GMT

        {
          "meta": {
            "code": 200
          },
          "response": {
            "deleted": true
          }
        }

    :qparam auth_token: Optional token for authentication if no :http:header:`Authorization` nor session cookie is sent.

    :reqheader Authorization: Optional token for authentication if no ``auth_token`` nor session cookie is sent.

    :param recordid: Which record to modify.
    :status 200: Successfully processed the query
    :status 400: Incorrect query.
    :status 403: No permission to alter a record associated with another user (e.g. not an ``editor``)
    """
    record = models.Record.query.filter_by(id=recordid).first()
    if record is None:
        raise InvalidUsage("No such record.", status_code=400)

    if record.user_id != current_user.id and not current_user.has_role('editor'):
        raise InvalidUsage("No access to the records of this user.", status_code=403)

    if request.method == 'GET':
        result = models.record_schema.dump(record)
        return jsonify(wrap200code(targets=result.data))
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
        result = models.record_schema.dump(record)
        return jsonify(wrap200code(record=result.data))
    elif request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        return jsonify(wrap200code(deleted=True))
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
