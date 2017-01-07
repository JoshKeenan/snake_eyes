from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail
from flask_wtf import CsrfProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel


debug_toolbar = DebugToolbarExtension()
mail = Mail()
csrf = CsrfProtect()
db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
babel = Babel()
