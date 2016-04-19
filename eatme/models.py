from flask import g
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin
from . import db, ma


# Define a base model for other database tables to inherit
class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())


# Define models
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(Base, RoleMixin):
    """
    Administrative roles
    """
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(Base, UserMixin):
    """
    User list
    """
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(45))
    current_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer)
    target_daily_calories = db.Column(db.Integer, default=0)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    records = db.relationship('Record', backref='users', lazy='dynamic')


class Record(Base):
    """
    Calories records
    """
    record_date = db.Column(db.Date())
    record_time = db.Column(db.Time())
    description = db.Column(db.Unicode(255))
    calories = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


"""
Output Schemas
"""


class UserSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id', 'email', 'date_created', 'date_modified', '_links')

    # Smart hyperlinking
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.users', userid='<id>'),
        'collection': ma.URLFor('api.users')
    })


user_schema = UserSchema()
users_schema = UserSchema(many=True)


class RecordSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id',
                  'date_created',
                  'date_modified',
                  'record_date',
                  'record_time',
                  'description',
                  'calories',
                  'user_id')


record_schema = RecordSchema()
records_schema = RecordSchema(many=True)


class TargetSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id', 'target_daily_calories')


target_schema = TargetSchema()
