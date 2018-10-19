import os

from pricealerts import environ

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_DIR=os.path.join(BASE_DIR,'pricealerts','templates')
# Log everything to the logs directory at the instance/logs folder
LOGFILE_ROOT = os.path.join(BASE_DIR , 'instance','logs')

# We are not going to use instance/pricealerts.sqlite as database
# DATABASE=os.path.join(app.instance_path, 'pricealerts.sqlite')

# Create a local.env file in the settings directory for api keys, passwords, etc
# But ideally this env file should be outside the git repo
env_file = os.path.join(BASE_DIR, 'instance', 'local.env')
if os.path.exists(env_file):
    environ.Env.read_env(str(env_file))

env = environ.Env()

SECRET_KEY=os.urandom(16)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # specify the maximum file size after which an upload is aborted
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'instance','photos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
JSON_AS_ASCII = False  # If False When using json.dumps() every non-ascii character won't be escaped
ALERT_UPDATE_TIMEOUT = env('ALERT_UPDATE_TIMEOUT', default=10) # in minutes
ALERT_CHECK_INTERVAL = env('ALERT_CHECK_INTERVAL', default=30) # in seconds
ADMINS_EMAIL = env('ADMINS_EMAIL').split(';')

EMAILS_ALLOWED = ['gmail.com', 'yahoo.com', 'outlook.com']
API_KEY = env('API_KEY')
API_BASE_URL = env('API_BASE_URL')

SMTP_SERVER=env('SMTP_SERVER')
SMTP_PORT=env('SMTP_PORT')
SMTP_USER=env('SMTP_USER')
SMTP_PASS=env('SMTP_PASS')
EMAIL_FROM = env('EMAIL_FROM')
