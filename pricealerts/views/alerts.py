import random

import requests
from bs4 import BeautifulSoup, SoupStrainer
from flask import Blueprint, url_for, request, flash, render_template
from flask_login import login_required, current_user
from werkzeug.utils import redirect

from pricealerts import StoreModel, ItemModel, AlertModel, UserModel
from pricealerts.forms import AlertForm
from pricealerts.models.model import StoreNotFoundError, ItemNotLoadedError
from pricealerts.settings import env, BASE_DIR, TEMPLATE_DIR

alert_blueprint = Blueprint('alerts', __name__, url_prefix='/alerts', template_folder='templates')


@alert_blueprint.route('/create', methods=['GET', 'POST'])
@login_required
def create_alert():
    form = AlertForm()

    validate = form.validate_on_submit()  # This is a shortcut for form.is_submitted() and form.validate().
    if request.method == 'GET':
        return render_template('store/new_alert.html', form=form)

    if validate:
        # Request method is POST
        prod_url = request.form['url']
        # store_id = int(request.form['store_id'])
        price_limit = float(request.form['price_limit'])
        check_frequency = int(request.form['check_frequency'])
        alert_email = request.form['alert_email']
        alert_phone = request.form['alert_phone']
        active = bool(request.form['active'])

        user = UserModel.find_one(username=current_user.username)

        try:
            store = StoreModel.find_by_url(prod_url)
        except StoreNotFoundError:
            only_title = SoupStrainer('title')
            # Find the store on Internet
            from urllib.parse import urlparse
            o = urlparse(prod_url)

            if o.netloc is None:
                location = o.path.split('/')[0]
            else:
                location = o.netloc

            store_url = o.scheme + "://" + location
            req = requests.get(store_url)
            html_doc = req.content
            soup = BeautifulSoup(html_doc, 'html.parser', parse_only=only_title)

            store = StoreModel(soup.title.string, store_url).save_to_db()

        # Create the item
        item = ItemModel.find_one(url=prod_url)
        if not item:
            try:
                item = ItemModel( prod_url, store=store).save_to_db()
            except ItemNotLoadedError as ex:
                flash(ex.message, category='error')
                return redirect(url_for('users.user_alerts'))

        # Create the alert
        alert = AlertModel(price_limit, item.id, user.id, check_every=check_frequency,
                   contact_email=alert_email, contact_phone=alert_phone,
                   active=active).save_to_db()


        alert.send_email_alert(subject="NEW ALERT CREATED from Pricing Alert Service <{}>".format(env('SMTP_USER')),
                               message="New Price Alert has been created for {}.<br>"
                                       "{} <{}> have setup this email address ({}) to receive alerts regarding prices"
                                       "drops over this product. <br/>"
                                       "You can now seat down and let us do "
                                       "the hard work".format(item.name,user.name,user.username, alert_email))

        #alert.send_sms_alert()

        # After saving all data redirect to user alerts page
        return redirect(url_for('users.user_alerts'))


    return render_template('store/new_alert.html', form=form)


@alert_blueprint.route('/edit/<int:alert_id>', methods=['GET', 'POST'])
@login_required
def edit_alert(alert_id):
    alert = AlertModel.find_by_id(alert_id)
    curr_url = alert.item.url
    if not alert:
        flash("Alert not found", category='error')
        return redirect(url_for('users.user_alerts'))

    form = AlertForm(request.form)

    if request.method == 'POST' and form.validate():
        form.populate_obj(alert)
        alert.item.url=curr_url
        alert.save_to_db()

        user = UserModel.find_one(username=current_user.username)
        try:
            alert.send_email_alert(subject="ALERT MODIFIED from Pricing Alert Service <{}>".format(env('EMAIL_FROM')),
                               message="New Price Alert has been updated for {}.<br>"
                                       "{} <{}> have setup this email address ({}) to receive alerts regarding prices"
                                       "drops over this product. <br/>"
                                       "You can now seat down and let us do "
                                       "the hard work".format(alert.item.name, user.name, user.username, alert.contact_email))
        except Exception:
            flash('Error sending email to {}. A notification has been '
                  'emitted to the system administrator'.format(alert.contact_emaiil), category='error')

        return redirect(url_for('users.user_alerts'))

    return render_template('store/edit_alert.html',
                           username=current_user.username if current_user.username is not None else 'Buyer',
                           alert=alert)



@alert_blueprint.route('/activate_deactivate/<int:alert_id>')
@login_required
def activate_deactivate_alert(alert_id):
    alert = AlertModel.find_by_id(alert_id)
    if alert:
        alert.active = not alert.active
        alert.save_to_db()
    return redirect(url_for('users.user_alerts'))
