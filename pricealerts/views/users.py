import datetime
import os

import pytz
from flask import request, render_template, url_for, flash, Blueprint, current_app
from flask_login import current_user, logout_user, login_required
from flask_login import login_user as session_login
from werkzeug.urls import url_parse
from werkzeug.utils import redirect, secure_filename

from pricealerts.forms import LoginForm, RegistrationForm
from pricealerts.models.model import UserErrors, ProfileModel
from pricealerts.models.model import UserModel

user_blueprint = Blueprint('users', __name__, url_prefix='/users', template_folder='templates')


@user_blueprint.route('/check_alerts/<string:user_id>')
@login_required
def check_user_alerts(user_id):
    pass


@user_blueprint.route('/myalerts', methods=['GET'])
@login_required
def user_alerts():
    # Look for the user's alerts and list them in the template
    alerts = current_user.get_alerts()
    for alert in alerts:
        alert.last_checked_delay = round((datetime.datetime.utcnow() - alert.last_checked).total_seconds() / 60, 2)
    return render_template('store/alerts.html', alerts=alerts)


#
# @user_blueprint.route('/login', methods=['GET', 'POST'])
# def login_user():
#
#     form = LoginForm()
#
#     validate = form.validate_on_submit() #  This is a shortcut for form.is_submitted()
#       (POST request) and form.validate().
#
#     if validate: # Checks if is POST and the form is valid
#         try:
#             UserModel.login_valid(request.form['email'], request.form['password'])
#
#         except UserError as loginEx:
#             session['username'] = None
#             flash(loginEx.message, category='error')
#             return render_template('store/login.html', form=form)
#
#         session['username'] = form.data['email']
#         return redirect(url_for('.user_alerts'))
#
#     return render_template('store/login.html', form=form)


@user_blueprint.route('/login', methods=['GET', 'POST'])
def login_user():
    if current_user.is_authenticated:
        return redirect(url_for('.user_alerts'))

    form = LoginForm()
    validate = form.validate_on_submit()  # This is a shortcut for form.is_submitted() and form.validate().

    if validate:  # Checks if is POST request and the form is valid
        try:
            user = UserModel.login_valid(form.data['email'], form.password.data)
            if user:
                session_login(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('.user_alerts')
                flash('User {0} logged in correctly'.format(user.name), 'success')
                return redirect(next_page)


        except UserErrors as loginEx:
            # Logout the user, just in case there is a session saved for this user previously
            logout_user()
            flash(loginEx.message, 'error')
            # return redirect(url_for('.login_user'))

    return render_template('user/login.html', title='Sign In', form=form)


@user_blueprint.route('/register', methods=['GET', 'POST'])
def register_user():
    form = RegistrationForm()  # data coming from client is got from request.form and request.files

    valid = form.validate_on_submit()  # Form is submitted using POST method and is valid data
    if valid:
        try:
            user = UserModel.register(form.data['email'], form.data['password'], form.data['name'], form.data['phone'])
            if user is not None:
                # After register, login in the user and redirecting to their alerts
                session_login(user)
                return redirect(url_for('.user_alerts'))
        except UserErrors as regError:
            flash(regError.message, 'error')
            # return redirect(url_for('.register_user'))

    print(form.data)
    print(form.email.errors)
    return render_template('user/register.html', title='Sign Up', form=form)


# @user_blueprint.route('/register',methods=['GET', 'POST'])
# def register_user():
#     form = RegistrationForm() # data coming from client is got from request.form and request.files
#
#     valid = form.validate_on_submit()
#     print(valid)
#     print(form.errors)
#     print(form.data)
#     if valid:
#         try:
#             if(UserModel.register(form.data['email'], form.data['password'], form.data['name'], form.data['phone'])):
#                 # After register, login in the user and redirecting to their alerts
#                 session['username'] = form.data['email']
#                 return redirect(url_for('.user_alerts'))
#         except UserError as regError:
#             flash(regError.message, category='error')
#             return redirect(url_for('.register_user'))
#
#     return render_template('store/register.html', title='Sign Up', form=form)

@user_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('.login_user'))


# @user_blueprint.route('/logout')
# def logout():
#     session['username'] = None
#     return redirect(url_for('.login_user'))

TZ_DATA = [(v, v) for v in pytz.common_timezones]

@user_blueprint.route('/me', methods=['GET'])
@user_blueprint.route('<string:slug>/', methods=['GET'])
@login_required
def user_profile(slug=None):
    kwargs = { }

    if slug:
        profile = ProfileModel.find_one(slug=slug)
        kwargs["show_user"] = profile.user
    else:
        kwargs["show_user"] = current_user

    if kwargs["show_user"] == current_user:
        kwargs["editable"] = True
    else:
        kwargs["editable"] = False


    return render_template('user/profile.html', **kwargs)

@user_blueprint.route('me/edit/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    error = None

    if request.method == 'POST':
        theme = request.form['theme']
        first_name = request.form.get('first_name', None)
        last_name = request.form.get('last_name', None)
        phone = request.form.get('phone', None)
        password = request.form.get('password', None)
        password2 = request.form.get('password2', None)
        picture = request.files.get('picture', None)
        bio = request.form.get('bio', None)
        tz = request.form.get('tz', None)

        if not first_name:
            error = 'First name is required.'
        elif not last_name:
            error = 'Last name is required.'
        elif not password:
            error = 'Last name is required.'
        elif password != password2:
            error = "Passwords do not match"
        elif not tz:
            error = 'Timezone must be selected'

        if error is None:
            current_user.name = first_name + " " + last_name
            current_user.phone = phone
            current_user.theme = theme
            current_user.set_password(password)
            if current_user.profile is None:
                current_user.profile = ProfileModel()

            current_user.profile.bio = bio
            current_user.profile.timezone = tz
            if picture is not None:
                filename = secure_filename(picture.filename)
                current_user.profile.picture = filename
                picture.save(os.path.join(current_app.instance_path, 'photos', filename))

            current_user.save_to_db()
            return redirect(url_for('users.edit_profile'))

        flash(error, category='error')

    first_name, last_name = current_user.name.split(" ")
    return render_template('user/edit_profile.html', user=current_user, first_name=first_name,
                           last_name=last_name, tz_data = TZ_DATA)