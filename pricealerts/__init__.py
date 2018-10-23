import base64
from logging.handlers import SMTPHandler

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.exceptions import BadRequest, NotFound
from logging.config import dictConfig
from pricealerts.settings import *
from pricealerts.db import db
from pricealerts.models import UserModel, ItemModel, StoreModel, AlertModel
import logging
LOGGING_CONFIG = None

def create_app(test_config=None):
    # Create logging config before Flask instance app is created
    # Reset logging
    # (see http://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/)

    logfile = os.path.join(LOGFILE_ROOT, 'project.log') if env('FLASK_ENV')=='production' \
                else  os.path.join(LOGFILE_ROOT, 'project-dev.log')

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
            'verbose': {
                'format':
                    "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
                'datefmt':
                    "%b/%d/%Y %H:%M:%S"
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
            'proj_log_handler': {
                'level': 'WARNING',
                'class': 'logging.FileHandler',
                'filename': logfile,
                'formatter': 'verbose'
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            }
        },

        'root': {
            'level': 'INFO',
            'handlers': ['wsgi', 'proj_log_handler']
        }
    }
    dictConfig(LOGGING)

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)



    # ensure the instance folder exists with photos and logs folders inside
    try:
        os.makedirs(app.instance_path)
        os.makedirs(os.path.join(app.instance_path, 'photos'), exist_ok=True)
        os.makedirs(os.path.join(app.instance_path, 'logs'), exist_ok=True)
    except OSError:
        pass

    # load the default settings instance config
    import pricealerts.settings
    app.config.from_object(pricealerts.settings)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('development.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    if env('FLASK_ENV')=='production':
        # Email Errors to Admins in production mode

        mail_handler = SMTPHandler(
            mailhost=(app.config['SMTP_SERVER'], app.config['SMTP_PORT']),
            fromaddr=app.config['EMAIL_FROM'],
            toaddrs=app.config['ADMINS_EMAIL'],
            subject='Application Error',
            credentials=(app.config['SMTP_USER'], app.config['SMTP_PASS']),
            timeout=app.config['EMAIL_SEND_TIMEOUT'])

        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(
            logging.Formatter(
                '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))

        app.logger.addHandler(mail_handler)

    # Flask-Login needs to be created and initialized right after the application instance
    # Docs OK: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
    loginmanager = LoginManager(app)

    # Flask-Login provides a very useful feature that forces users to log in before they can view certain pages of the
    # application. If a user who is not logged in tries to view a protected page, Flask-Login will automatically redirect
    # the user to the login form, and only redirect back to the page the user wanted to view after the login process is complete.
    # Flask-Login needs to know what is the view function that handles logins.
    loginmanager.login_view = 'users.login_user'

    @loginmanager.user_loader
    def load_user(id):
        return UserModel.query.get(int(id))

    @loginmanager.request_loader
    def load_user_from_request(request):

        # first, try to login using the api_key url arg
        api_key = request.args.get('api_key')
        if api_key:
            user = UserModel.query.filter_by(api_key=api_key).first()
            if user:
                return user

        # next, try to login using Basic Auth
        api_key = request.headers.get('Authorization')
        if api_key:
            api_key = api_key.replace('Basic ', '', 1)
            try:
                api_key = base64.b64decode(api_key)
            except TypeError:
                pass
            user = UserModel.query.filter_by(api_key=api_key).first()
            if user:
                return user

        # finally, return None if both methods did not login the user
        return None


    # Initialize bootstrap
    Bootstrap(app)

    # https://flask-wtf.readthedocs.io/en/stable/csrf.html
    # To enable CSRF protection globally for a Flask app, register the CSRFProtect extension.
    csrf = CSRFProtect(app)

    @app.errorhandler(CSRFError)
    def errorHandler(reason):
        """
        Register a function that will generate the response for CSRF errors.
        Due to historical reasons, the function may either return a response or raise an exception with flask.abort().
        :param error: CSRFError instance
        :return: Template rendered with the reason
        """
        return render_template('error.html', code=400, reason=reason)

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return render_template('error.html', code=400, reason=e.description)

    @app.errorhandler(NotFound)
    def handle_not_found(e):
        return render_template('error.html', code=404, reason='Opps Page is not available !')
    # Register db with the Application and initialize database tables
    db.init_app(app)

    if app.config['ENV'] == 'development':
        @app.before_first_request
        def recreate_all_tables():
            db.drop_all()
            db.create_all()

            # Create initial data
            user = UserModel.find_by(username='alexmtnezf@gmail.com')
            if not user:
                user = UserModel('Alex Martinez', 'alexmtnezf@gmail.com', '123456', is_admin=True, api_key=os.urandom(35))
                db.session.add(user)
                db.session.commit()

    if app.config['ENV'] == 'production':
        @app.before_first_request
        def create_all_tables():
            db.create_all()

            # Create initial data
            user = UserModel.find_by(username='alexmtnezf@gmail.com')
            if not user:
                user = UserModel('Alex', 'alexmtnezf@gmail.com', '123456', is_admin=True, api_key=os.urandom(35))
                db.session.add(user)
                db.session.commit()


    # Register views with blueprints
    from .views.users import user_blueprint
    from .views.alerts import alert_blueprint
    from .views.globals_views import global_bp

    app.register_blueprint(user_blueprint)
    app.register_blueprint(alert_blueprint)
    app.register_blueprint(global_bp)

    return app
