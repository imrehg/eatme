"""
Management tools for EatMe
"""
from flask.ext.script import Server, Shell, Manager, prompt_pass
from flask.ext.security.utils import encrypt_password

# Import relevant parts of the app
from eatme import app, db, models

manager = Manager(app)

# Run development server
manager.add_command("runserver", Server())

# Add shell
def _make_context():
    return dict(app=app, db=db, models=models)

manager.add_command("shell", Shell(make_context=_make_context))

@manager.command
def genpwhash():
    """
    Generate password hash for input
    """
    print("Current password hash algorithm: {}".format(app.config['SECURITY_PASSWORD_HASH']))
    password = prompt_pass("Enter password to hash (hidden)")
    print(encrypt_password(password))


if __name__ == "__main__":
    manager.run()
