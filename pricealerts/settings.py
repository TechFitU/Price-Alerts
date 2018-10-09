import os

from pricealerts import environ

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_DIR=os.path.join(BASE_DIR,'pricealerts','templates')

# Create a local.env file in the settings directory
# But ideally this env file should be outside the git repo
env_file = os.path.join(BASE_DIR, 'instance', 'local.env')
if os.path.exists(env_file):
    environ.Env.read_env(str(env_file))

env = environ.Env()

ENV = env('FLASK_ENV', default='development')  # same as: os.environ['FLASK_ENV'] = True
DEBUG = env('FLASK_DEBUG', default=True)

if ENV == 'development':
    SQLALCHEMY_DATABASE_URI = env('DATABASE_URL',
                         default='sqlite:///{}pricealerts.sqlite'.format(os.path.join(BASE_DIR, 'instance/')))
if ENV == 'production':
    SQLALCHEMY_DATABASE_URI = env(
        'DATABASE_URL', default='postgresql://test:test@localhost:5432/store')

JSON_AS_ASCII = False  # If False When using json.dumps() every non-ascii character won't be escaped

SQLALCHEMY_TRACK_MODIFICATIONS = True
PROPAGATE_EXCEPTIONS = True
SQLALCHEMY_ECHO = True if bool(DEBUG) is True else False
ALERT_UPDATE_TIMEOUT = env('ALERT_UPDATE_TIMEOUT', default=10) # in minutes
ALERT_CHECK_INTERVAL = env('ALERT_CHECK_INTERVAL', default=30) # in seconds

EMAILS_ALLOWED = ['gmail.com', 'example.com']
API_KEY = env('API_KEY')
API_BASE_URL = env('API_BASE_URL')
EMAIL_FROM = env('EMAIL_FROM')
