DEBUG = False
DATABASE_URI = 'sqlite://'
SQLALCHEMY_TRACK_MODIFICATIONS = False

## Security settings
SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authorization'
SECRET_KEY = 'i-have-not-changed-the-secret-key'
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = 'i-have-not-changed-the-salt'
SECURITY_TOKEN_AUTHENTICATION_KEY = 'auth_token'
SECURITY_TOKEN_MAX_AGE = None
SECURITY_TRACKABLE = True
# Note: http://mandarvaze.github.io/2015/01/token-auth-with-flask-security.html
WTF_CSRF_ENABLED = False

ADMIN_EMAIL = 'root@localhost'
ADMIN_PASSWORD_HASH = '$2a$12$nTdjqiAwDXbCm3xtv2TkReaNtWXBLnqSDUu72v/JHgSkmfgSUw.pO'

## Mail settings
MAIL = False   # Mail functionality disabled by default
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'username'
MAIL_PASSWORD = 'password'