"""
Management tools for EatMe
"""
from flask.ext.script import Server, Shell, Manager

# Import relevant parts of the app
from eatme import app, db, models

manager = Manager(app)

# Run development server
manager.add_command("runserver", Server())

# Add shell
def _make_context():
    return dict(app=app, db=db, models=models)

manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()
