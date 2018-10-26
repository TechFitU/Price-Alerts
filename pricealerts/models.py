# -*- coding: utf-8 -*-
"""
common/item.py

Module that contains the model definition for every table in a SQLAlchemy database.
"""
import datetime
import os
import re
import uuid
import random
import string
import requests
import sqlalchemy
from bs4 import BeautifulSoup, SoupStrainer
from flask import json
from flask.globals import current_app
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound
from twilio.base.exceptions import TwilioRestException
from werkzeug.exceptions import NotFound

from pricealerts import settings
from pricealerts.db import db
from pricealerts.common.base_model import BaseModel, DatabaseError
from pricealerts.settings import env
from pricealerts.utils import notifications
from pricealerts.utils.helpers import parse_phone, is_valid_email
from pricealerts.utils.notifications import NotificationDispatcher


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
        try:

            return self.items.filter_by(id=item_id).first_or_404()
        except NotFound:
            raise ItemNotFoundError('Item not found in the store')

    def delete_item(self, item_id):
        try:
            item = self.items.filter_by(id=item_id).first_or_404()
        except NotFound:

            raise ItemNotFoundError('Item not found in the store')

        self.items.remove(item)  # same as: item.delete_from_db()

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
    image = db.Column(db.String(255), nullable=True)
    alerts = db.relationship('AlertModel', backref=db.backref('item', lazy='joined'), lazy='dynamic',
                             cascade="all, delete, delete-orphan")
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)

    def __init__(self, url, store_id, name=None,price=None, created=None, created_by=None, updated=None, updated_by=None):
        self.url = url
        self.name = name
        self.store_id = store_id
        self.price = price

    def __str__(self):
        return "Item(id='%s', name='%s')" % (self.id, self.name)

    def json(self):
        return {
            'name': self.name,
            'price': self.price,
            'store_id': self.store_id,
            'url' : self.url
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
        only_price_img_and_title_tag_ = SoupStrainer(name=['title', 'p', 'span', 'img'])


        req = requests.get(self.url)


        if req.status_code == 200:
            html_doc = req.content
            soup = BeautifulSoup(html_doc, 'html.parser', parse_only=only_price_img_and_title_tag_)

            # Get price from ebay.com
            element = soup.find('span', attrs={'itemprop':'price'})
            if element is None:
                # Get price from johnlewis.com
                element =soup.find('p', class_={'price price--large'})
            if element is None:
                element = soup.find('span', attrs={'aria-label':re.compile('price')})

            price = matcher.search(element.text.strip())
            if price is not None:
                price = float(price.group(1))


            name = soup.find(name="title").string

            # item image for johnlewis.com
            image = soup.find("img", attrs={'alt':re.compile(name)})
            if image is not None:
                image = image.get('src')
            return name, price, image

        codes = {404: 'Not found', 403: 'Permission denied', 500:'Internal server error'}
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
    contact_email = db.Column(db.String(80), nullable=False)
    check_every = db.Column(db.Integer, default=10, nullable=False)
    last_checked = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.datetime.utcnow())


    def __str__(self):
        return "(AlertModel<id={}, user='{}', item='{}'>)".format(self.id, self.user.name, self.item.name)

    def __init__(self, price_limit, item_id, user_id, contact_email,
                 active=True, shared=False, contact_phone=None,
                 last_checked=None, check_every=10):
        self.price_limit = price_limit
        self.item_id = item_id
        self.user_id = user_id
        self.last_checked = last_checked
        self.check_every = check_every
        self.contact_email = contact_email if contact_email is not None else 'undefined'
        self.contact_phone = contact_phone
        self.shared = shared
        self.active = active
        self.last_checked_delay = None

    def json(self):
        return {
            'id': self.id,
            'price_limit': self.price_limit,
            'last_checked': self.last_checked,
            'check_every': self.check_every,
            'item_id': self.item_id,
            'item': self.item.name if self.item is not None else None,
            'user_id': self.user_id,
            'user': self.user.name if self.user is not None else None,
            'active': self.active,
            'shared': self.shared,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email
        }

    def send_email_alert(self, subject, message):
        return notifications.NotificationDispatcher.send_email(self.user.name, self.user.username, self.contact_email,
                                                               subject, message)

    def send_sms_alert(self):
        return notifications.NotificationDispatcher.send_sms(
                from_name="Pricing Alert Service",
                to_phone=self.contact_phone,
                to_name=self.user.name,
                text='New Alert for {} and price {} was added.'.format(
                    self.item.name, self.item.price))



    # Class methods
    @classmethod
    def find_needing_update(cls, minutes_since_last_update=env('ALERT_CHECK_INTERVAL',default=10)):
        last_update_limit = datetime.datetime.utcnow() - datetime.timedelta(minutes=int(minutes_since_last_update))
        return cls.query.filter(AlertModel.active == True, AlertModel.last_checked <= last_update_limit).all()

    def load_price_change(self):
        try:
            self.item.name, self.item.price, self.item.image = self.item.load_item_data()
        except:
            pass
        self.last_checked = datetime.datetime.utcnow()

        try:
            self.save_to_db()
        except:
            pass

    def send_email_if_price_limit_reached(self):
        if self.item.price < self.price_limit:
            subject = "NEW ALERT FOR PRICE DROP from TechFitU <{}>".format(env('SMTP_USER')),
            message = "!Congratulations {}, you have a chance to save money !<br/>"
            "The product {} has dropped its price. "
            "Got to the product <a href='{}'>link</a> to see its currrent status"
            " You are a truly awesome prices hunter!".format(self.contact_email,
                                                             self.item.name,
                                                             self.item.url)

            return NotificationDispatcher.send_email(self.user.name, self.user.username, self.contact_email,
                                              subject=subject, message=message)

        return False



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

class RegisteredUserError(UserErrors):
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
    api_key = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime(timezone=False), nullable=True)

    alerts = db.relationship('AlertModel', lazy=True, backref='user',
                             cascade="all, delete, delete-orphan")

    profile = db.relationship("ProfileModel", uselist=False, back_populates='user')

    def __init__(self, name, username, password, api_key=None, phone=None, is_admin=False, is_staff=False, roles=None,
                 theme = None, last_login = None):
        self.username = username

        self.api_key="".join([random.SystemRandom().choice(string.digits + string.ascii_letters + string.punctuation) for i in
                       range(100)]).replace("&", "*") if api_key is None else api_key
        self.name = name
        self.password = generate_password_hash(password)  # Encrypt password before save it
        self.is_admin = is_admin
        self.is_staff = is_staff
        self.phone = "-".join(parse_phone(phone)) if isinstance(phone, str) and phone != '' else None
        self.roles = list() if roles is None else roles
        self.theme = theme
        self.last_login = last_login


    def __str__(self):
        return "User(id='%s')" % self.id

    def json(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'is_admin': self.is_admin,
            'is_staff': self.is_staff,
            'phone': self.phone,
            'last_login': self.last_login,
            'theme': self.theme
        }

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
            user = cls(name=name, password=password, username=email, phone=phone, api_key=os.urandom(35))
            try:
                user.save_to_db()
            except DatabaseError as ex:
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
        try:
            return cls.query.filter_by(username=username).first()
        except OperationalError as ex:
            current_app.logger.error('Data was not found. Error: {}'.format(str(ex)))
            raise DatabaseError('Data was not found.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error('Database operation error. SQL executed: {}\nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Database or tables was not found.')


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