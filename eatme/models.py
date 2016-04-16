from flask import g
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, ma

# Define a base model for other database tables to inherit
class Base(db.Model):

    __abstract__  = True

    id            = db.Column(db.Integer, primary_key=True)
    date_created  = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                                           onupdate=db.func.current_timestamp())


class User(Base):
    __tablename__ = 'auth_user'

    username = db.Column(db.String(128), unique=True)
    # Identification Data: email & password
    password_hash = db.Column(db.String(192), nullable=False)

    # Authorisation Data: role & status
    # role = db.Column(db.SmallInteger, nullable=False)
    # status = db.Column(db.SmallInteger, nullable=False)

    def __init__(self, username, password, password_hash=None):
        self.username = username
        if len(password) > 0:
            self.set_password(password)
        elif password_hash is not None:
            assert isinstance(password_hash, str)
            self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username

class UserSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id', 'username', 'date_created', 'date_modified', '_links')
    # Smart hyperlinking
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.users', userid='<id>'),
        'collection': ma.URLFor('api.users')
    })

user_schema = UserSchema()
users_schema = UserSchema(many=True)