"""Shared extension objects, created here and attached to the app in create_app().

Created without an app so any module can import them without circular imports.
Rails equivalent: the framework wires these up for you (ActiveRecord, migrations);
in Flask you instantiate and register each one yourself.
"""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
