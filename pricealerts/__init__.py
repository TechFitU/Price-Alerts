import os

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_wtf.csrf import CSRFError, CSRFProtect

from pricealerts.db import db
from pricealerts.models.model import UserModel, ItemModel, StoreModel, AlertModel


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(

        SECRET_KEY=os.urandom(16),  # SECURITY WARNING: keep the secret key used in production secret!
        # im not going to use instance/pricealerts.sqlite as database
        # DATABASE=os.path.join(app.instance_path, 'pricealerts.sqlite'),
    )


    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # load the default settings instance config
    app.config.from_object('pricealerts.settings')
    #
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)


    # Flask-Login needs to be created and initialized right after the application instance
    # Docs OK: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
    login = LoginManager(app)

    # Flask-Login provides a very useful feature that forces users to log in before they can view certain pages of the
    # application. If a user who is not logged in tries to view a protected page, Flask-Login will automatically redirect
    # the user to the login form, and only redirect back to the page the user wanted to view after the login process is complete.
    # Flask-Login needs to know what is the view function that handles logins.
    login.login_view = 'users.login_user'

    @login.user_loader
    def load_user(id):
        return UserModel.query.get(int(id))

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
        return render_template('error.html', reason=reason)

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
                user = UserModel('Alex Martinez', 'alexmtnezf@gmail.com', '123456', is_admin=True)
                db.session.add(user)
                db.session.commit()

    if app.config['ENV'] == 'production':
        @app.before_first_request
        def create_all_tables():
            db.create_all()

            # Create initial data
            user = UserModel.find_by(username='alexmtnezf@gmail.com')
            if not user:
                user = UserModel('Alex', 'alexmtnezf@gmail.com', '123456', is_admin=True)
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
