from flask import (
    Blueprint, render_template, jsonify)
from flask_login import current_user, login_required

global_bp = Blueprint('site', __name__)


@global_bp.route('/')
@global_bp.route('/home')
def home():
    return render_template('store/home.html',
                           current_user=current_user)


@global_bp.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    return render_template('store/contact.html')


@global_bp.route('/about')
def about():
    return render_template('store/about.html')


@global_bp.route('/json')
def json():
    return jsonify({'message': "Hello, World!"})

# a simple page that says hello
@global_bp.route('/hello')
def hello():
    return 'Hello, World!'
