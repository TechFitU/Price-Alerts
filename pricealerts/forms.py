import decimal

from flask import url_for
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import (StringField, BooleanField, PasswordField, DecimalField, IntegerField, HiddenField)
from wtforms.validators import (DataRequired, Length, InputRequired, Email, EqualTo, Optional, ValidationError, URL, \
    NumberRange)
from pricealerts.models import UserModel
from pricealerts.utils.helpers import parse_phone, is_safe_url, get_redirect_target
from .widgets import MyTextInput, CustomPasswordInput


class RedirectForm(FlaskForm):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        super(RedirectForm, self).__init__(*args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))

class LoginForm(RedirectForm):
    email = StringField('Email Address',
                        validators=[DataRequired(), Email(), Length(min=6, max=35)], widget=MyTextInput(),
                        render_kw={'class': 'form-control', 'placeholder': 'Email address'})
    password = PasswordField('Password', description='Password',
                             validators=[DataRequired(), Length(min=6, max=512)], widget=CustomPasswordInput())
    remember_me = BooleanField('Remember me', validators=[InputRequired()], default=True)

    class Meta:
        csrf = True
        locales = ('en_US', 'es_MX')


# length function-based decorator to create a validator for length, as we are creating a callable needed by wtfforms.
# def length(min=-1, max=-1, message=None):
#     message = 'Must be between %d and %d characters long.' % (min, max) if message is None else message
#
#     def _length(form, field):
#         l = field.data and len(field.data) or 0
#         if l < min or max != -1 and l > max:
#             raise ValidationError(message)
#
#     return _length

# We converted our length validator function to a class-based decorator
class LengthValidator(object):
    def __init__(self, min=-1, max=-1, message=None):
        self.min = min
        self.max = max
        if not message:
            message = u'Field must be between %i and %i characters long.' % (min, max)
        self.message = message

    def __call__(self, form, field):
        l = field.data and len(field.data) or 0
        if l < self.min or self.max != -1 and l > self.max:
            raise ValidationError(self.message)


def email_validator(emails=None):
    if emails is None:
        emails = []

    emails = "( {} )".format("|".join(emails)) if len(emails) > 0 else r"[\w]+"

    def _email_validator(form, field):
        """
        This validator is added to the validators chain of the email field.
        :param form: The wtforms.form.Form object
        :param field: The email field of this form
        :return: raise a ValidationError if a validation error exists, otherwise None
        """
        user = UserModel.find_by_username(field.data)
        if user is not None:
            raise ValidationError('Already exists. Please use a different email address.')

        import re
        # # Define pattern matcher to detect valid emails
        pattern = r'^([\w-]+\.?)+@([\w-]+\.?)*(gmail.com|example.com)$'.format(emails)

        matcher = re.compile(pattern)

        if not matcher.match(field.data):
            raise ValidationError('Email address only can be in these domains: {0}'.format(emails))

    return _email_validator


def phone_validator():
    def _phone_validator(form, field):
        if not parse_phone(field.data):
            raise ValidationError('Phone number is not a valid phone')

    return _phone_validator


def name_validator():
    def _name_validator(form, field):
        if UserModel.find_by_name(field.data) is not None:
            raise ValidationError('Already exists. Please use a different name.')

    return _name_validator


class RegistrationForm(FlaskForm):

    name = StringField('Name', validators=[DataRequired(), LengthValidator(min=4, max=75), name_validator()],
                       widget=MyTextInput())
    email = StringField('Email Address',
                        validators=[DataRequired(), Email(), email_validator(['gmail.com', 'example.com']),
                                    LengthValidator(min=6, max=35)], widget=MyTextInput())

    phone = StringField('Phone', validators=[Optional(), phone_validator()], widget=MyTextInput())
    password = PasswordField('New Password', validators=[DataRequired(), LengthValidator(min=6, max=35)],
                             widget=CustomPasswordInput())
    confirm = PasswordField('Repeat Password',
                            validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
                            widget=CustomPasswordInput())
    accept_rules = BooleanField('I accept the site rules', validators=[DataRequired()], default=True)

    class Meta:
        csrf = True  # Explicit better than implicit
        locales = ('en_US', 'es_MX')


class AlertForm(FlaskForm):
    url = StringField('Product url', validators=[DataRequired(), URL()], widget=MyTextInput())
    price_limit = DecimalField('Price limit', places=2, rounding=decimal.ROUND_UP,
                               validators=[DataRequired(), NumberRange(2, 100000.00)], widget=MyTextInput())

    check_frequency = IntegerField('Check frequency',
                                   widget=MyTextInput(),
                                   validators=[DataRequired(),
                                               NumberRange(min=5, max=10,
                                                           message="This number must be between 5 and 10 minutes")])

    alert_email = StringField('Contact Email', _name='alert_email',
                        validators=[DataRequired(), Email(), LengthValidator(min=6, max=35)], widget=MyTextInput(),
                              render_kw={'type':'email'})

    alert_phone = StringField('Contact Phone', validators=[Optional(), phone_validator()], widget=MyTextInput())

    active = BooleanField('Active', validators=[DataRequired()], default=True,
                          render_kw={'class':'form-check-input', 'id':'defaultCheck1'})