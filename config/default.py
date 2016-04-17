DEBUG = False
DATABASE_URI = 'sqlite://'
SQLALCHEMY_TRACK_MODIFICATIONS = False

## Security settings
SECRET_KEY = 'i-have-not-changed-the-secret-key'
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = 'i-have-not-changed-the-salt'
SECURITY_TOKEN_AUTHENTICATION_KEY = 'auth_token'
SECURITY_TRACKABLE = True
# Note: http://mandarvaze.github.io/2015/01/token-auth-with-flask-security.html
WTF_CSRF_ENABLED = False

ADMIN_EMAIL = 'root@localhost'
ADMIN_PASSWORD_HASH = '$2a$12$nTdjqiAwDXbCm3xtv2TkReaNtWXBLnqSDUu72v/JHgSkmfgSUw.pO'

