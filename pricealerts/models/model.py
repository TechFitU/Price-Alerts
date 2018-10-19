# -*- coding: utf-8 -*-
"""
models/item.py

Module that contains the model definition for every table in a SQLAlchemy database.
"""
import datetime
import os
import re
import uuid

import pytz
import requests
from bs4 import BeautifulSoup, SoupStrainer
from flask import json
from flask.globals import current_app
from sqlalchemy.orm.exc import NoResultFound
from twilio.base.exceptions import TwilioRestException

from pricealerts import settings
from pricealerts.db import db
from pricealerts.models.base_model import BaseModel
from pricealerts.settings import env
from pricealerts.utils import notifications
from pricealerts.utils.helpers import parse_phone


class ItemNotFoundError(Exception):
    """
    Indicates that an item could not be found in the database
    """

    def __init__(self, message):
        self.message = message


class StoreNotFoundError(Exception):
    """
    Indicates that a store could not be found in the database
    """

    def __init__(self, message):
        self.message = message


class StoreModel(db.Model, BaseModel):
    """
    StoreModel class
    """
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    url_prefix = db.Column(db.String(80), unique=True)
    tag_name = db.Column(db.String(10))
    query_string = db.Column(db.String(75))

    items = db.relationship('ItemModel', lazy='dynamic', backref='store',
                            cascade="all, delete, delete-orphan")

    def __init__(self, name, url_prefix, tag_name="p", query_string=None):
        self.name = name
        self.url_prefix = url_prefix
        self.tag_name = tag_name
        self.query_string = json.dumps(query_string) \
            if query_string is not None else json.dumps({'class': 'price price--large'})

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'items': [item.json() for item in self.items.all()]
        }

    def get_item(self, item_id):
        return self.items.find_by_id(item_id)

    def delete_item(self, id):
        item = self.items.find_by(id=id, store_id=self.id)
        if item:
            self.items.remove(item)  # same as: item.delete_from_db()
        else:
            raise Exception()

    @classmethod
    def find_by_url_prefix(cls, url_prefix):
        return cls.query.filter_by(url_prefix=url_prefix).first()

    @classmethod
    def find_by_url(cls, url):
        """
        Return a store from a url like: https://www.johnlewis.com/john-lewis-partners-amber-copper-swirl-bauble-orange/p3539788
        :param url: The item's valid URL
        :return: a Store, if found, otherwise raises an exception
        """
        store = None

        from urllib.parse import urlparse
        o = urlparse(url)

        if o.netloc is None:
            location = o.path.split('/')[0]
        else:
            location = o.netloc

        store = cls.query.filter(cls.url_prefix.ilike('%{}%'.format(location))).first()
        if not store:
            raise StoreNotFoundError('Store not found with the url provided')

        return store


class ItemNotLoadedError(Exception):
    def __init__(self, message):
        self.message = message


class ItemModel(db.Model, BaseModel):
    """
    ItemModel class
    """

    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    price = db.Column(db.Float(precision=2), nullable=False, default=0.0)
    url = db.Column(db.String(255), nullable=True)
    tag_name = db.Column(db.String(10))
    query_string = db.Column(db.String(75))
    image = db.Column(db.String(255), nullable=True)

    alerts = db.relationship('AlertModel', backref=db.backref('item', lazy='joined'), lazy='dynamic',
                             cascade="all, delete, delete-orphan")
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)

    def __init__(self, name, url, price=None):
        self.url = url
        self.store = StoreModel.find_by_url(url)
        try:
            self.name, self.price, self.image = self.load_item_data()
        except:
            raise

        self.tag_name = self.store.tag_name
        self.query_string = self.store.query_string

    def json(self):
        return {
            'name': self.name,
            'price': self.price,
            'store_id': self.store_id
        }

    def load_item_data(self):
        """
        Load an item's name using their store, the html page information, and passing the tag name and the query to
        find where the item price is located in the web page, setting up the price for the imte in the database
        :return: The item updated
        """
        matcher = re.compile('''
                # # don't match beginning of string, the price can start anywhere
        (\d+\.\d+)  # try to match float numbers
        \D*         # optional separator is any number of non-digits
        (\d+\.\d+)? # optional price boundary, try to match float numbers is a price range, ie: 45.00 - 55.12 
        ''', re.VERBOSE)
        only_price_and_title_tag_ = SoupStrainer(name=['title', 'p', 'span', 'img'])


        req = requests.get(self.url)


        if req.status_code == 200:
            html_doc = req.content
            soup = BeautifulSoup(html_doc, 'html.parser', parse_only=only_price_and_title_tag_)

            # Get price from ebay.comjohnlewis.com
            element = soup.find('span', attrs={'itemprop':'price'})
            if element is None:
                # Get price from
                element =soup.find('p', class_={'price price--large'})
            if element is None:
                element = soup.find('span', attrs={'aria-label':re.compile('price')})


            price = matcher.search(element.text.strip())
            if price is not None:
                price = float(price.group(1))

            name = soup.find(name="title").string

            image = None  # soup.find("img", attrs={'alt':name}).src
            return name, price, image

        codes = {404: 'Not found', 403: 'Permission denied'}
        raise ItemNotLoadedError('Product page not loaded correctly: {}'.format(codes[req.status_code]))


class AlertModel(db.Model, BaseModel):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    price_limit = db.Column(db.Float(precision=2), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    shared = db.Column(db.Boolean, default=False, nullable=False)
    contact_phone = db.Column(db.String(30), nullable=True)
    contact_email = db.Column(db.String(80), nullable=True)
    check_every = db.Column(db.Integer, default=10, nullable=False)
    last_checked = db.Column(db.DateTime(timezone=False), nullable=True)

    def __init__(self, price_limit, item_id, user_id,
                 active=True, shared=False, contact_phone=None, contact_email=None,
                 last_checked=None, check_every=10):
        self.price_limit = price_limit
        self.item_id = item_id
        self.user_id = user_id
        self.last_checked = datetime.datetime.utcnow() if last_checked is None else last_checked
        self.last_checked_delay = (datetime.datetime.utcnow() - self.last_checked).total_seconds() / 60
        self.check_every = check_every
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.shared = shared
        self.active = active

    def send_sms_alert(self):
        try:
            notifications.NotificationDispatcher.send_sms(
                from_name="Pricing Alert Service",
                to_phone=self.contact_phone,
                to_name=self.user.name,
                text='New Alert for {} and price {} was added.'.format(
                    self.item.name, self.item.price))
        except TwilioRestException as ex:
            print(ex.msg)
            pass


    def __send_simple_message(self):
        """
        Real call to send emails using my own domain
        :return: HttpResponse object
        """
        return requests.post(
            current_app.config['API_BASE_URL'],
            auth=("api", current_app.config['API_KEY']),
            data={"from": "Excited User <admin@techfitu.com>",
                  "to": ["alexmtnezf@gmail.com", "admin@techfitu.com"],
                  "subject": "Hello",
                  "text": "Testing some Mailgun awesomness!"})
        # You can see a record of this email in your logs: https://app.mailgun.com/app/logs


    # Class methods
    @classmethod
    def find_needing_update(cls, minutes_since_last_update=env('ALERT_UPDATE_INTERVAL',default=10)):

        last_update_limit = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes_since_last_update)
        return cls.query.filter(AlertModel.active == True, AlertModel.last_checked <= last_update_limit).all()

    def load_price_change(self):
        try:
            self.item.load_item_data()
        except:
            pass
        self.last_checked = datetime.datetime.utcnow()

        self.save_to_db()

    def send_email_if_price_limit_reached(self):
        if self.item.price < self.price_limit:
            self.send_email_alert(subject="NEW ALERT FOR PRICE DROP from TechFitU <{}>".format(env('SMTP_USER')),
                                  message="!Congratulations {}, you have a chance to save money !<br/>"
                                          "The product {} has dropped its price. "
                                          "Got to the product <a href='{}'>link</a> to see its currrent status"
                                          " You are a truly awesome prices hunter!".format(self.contact_email,
                                                                                           self.item.name,
                                                                                           self.item.url))

    def send_email_alert(self, subject, message):

        notifications.NotificationDispatcher.send_email(self.user.name, self.user.username, self.contact_email,
                                                            subject=subject, message=message)



class TokenNotFound(Exception):
    """
    Indicates that a token could not be found in the database
    """
    pass


class TokenModel(db.Model, BaseModel):
    __tablename__ = 'jwt_tokens'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    token_type = db.Column(db.String(10), nullable=False)
    user_identity = db.Column(db.String(50), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    expires = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def json(self):
        return {
            'token_id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'user_identity': self.user_identity,
            'revoked': self.revoked,
            'expires': self.expires
        }

    def __init__(self, jti, token_type, user_identity, expires, revoked):
        self.jti = jti
        self.token_type = token_type
        self.user_identity = user_identity
        self.expires = expires
        self.revoked = revoked

    @classmethod
    def is_jti_blacklisted(cls, decrypted_token):
        try:
            token = cls.query.filter_by(jti=decrypted_token['jti']).first()
            return token.revoked
        except NoResultFound:
            return True


from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
#from pricealerts.utils.helpers import generate_password_hash, check_password_hash, parse_phone


class UserErrors(Exception):
    def __init__(self, message):
        self.message = message


class UserNotFoundError(UserErrors):
    pass


class IncorrectPasswordError(UserErrors):
    pass


class RegisterUserError(UserErrors):
    pass


class UserModel(db.Model, UserMixin, BaseModel):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(
        db.String(512), nullable=False
    )  # OJO: no podemos dejar de ponerle maxlength en SQLite a los campos de tabla
    phone = db.Column(db.String(30), nullable=True)
    is_admin = db.Column(db.Boolean(), default=False)
    is_staff = db.Column(db.Boolean(), default=False)
    theme = db.Column(db.String(150), nullable=True)
    alerts = db.relationship('AlertModel', lazy=True, backref='user',
                             cascade="all, delete, delete-orphan")

    profile = db.relationship("ProfileModel", uselist=False, back_populates='user')

    def __init__(self, name, username, password, phone=None, is_admin=False, is_staff=False, roles=None):
        self.username = username
        self.name = name
        self.password = generate_password_hash(password)  # Encrypt password before save it
        self.is_admin = is_admin
        self.is_staff = is_staff
        self.phone = "-".join(parse_phone(phone)) if isinstance(phone, str) and phone != '' else None
        self.roles = list() if roles is None else roles


    def __str__(self):
        return "User(id='%s')" % self.id

    def json(self):
        return {'id': self.id, 'username': self.username, 'name': self.name}

    def get_alerts(self):
        return self.alerts

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha512')  # default method is pbkdf2:sha256

    def check_password(self, password):
        return check_password_hash(self.password, password)

    # Class methods
    @classmethod
    def register(cls, email, password, name, phone=None):
        user = cls.find_by_username(email)

        if user is None:
            user = cls(name=name, password=password, username=email, phone=phone)
            try:
                user.save_to_db()
            except Exception as ex:
                raise RegisterUserError(str(ex))

        return user

    @classmethod
    def login_valid(cls, email, password):
        """
        This function checks if the email and password are correct, first looks for the user in database,
        if there is match then checks if the user's password in database is actually the same as the one sent in the form.
        :param email: User's email
        :param password: User's sha512 hashed password
        :return: True if email and password match, False otherwise
        """

        user = cls.find_one(username=email)
        if not user:
            raise UserNotFoundError("The user %s not found." % email)

        if not check_password_hash(user.password, password):
            raise IncorrectPasswordError("Password sent doesn't match with the user's password")

        return user

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()


class BaseProfile(db.Model):
    __tablename__ = "profiles"

    slug = db.Column(db.String(64), primary_key=True, default = uuid.uuid4)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    user = db.relationship("UserModel", back_populates='profile')

    type= db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'profiles'
    }

class ProfileModel(BaseProfile, BaseModel):

    picture = db.Column(db.String(64), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    email_verified = db.Column(db.Boolean(), default=True)
    timezone = db.Column(db.String(32), default=settings.TIME_ZONE)

    __mapper_args__ = {
        'polymorphic_identity': 'profile'
    }

    def __str__(self):
        return "{}'s profile". format(self.user)