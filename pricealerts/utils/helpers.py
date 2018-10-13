# -*- coding: utf-8 -*-
import functools
import re
import time

from flask import request
from passlib.handlers.pbkdf2 import pbkdf2_sha512


def secure_cookie():
    """Return true if cookie should have secure attribute"""
    return request.environ.get('wsgi.url_scheme', None) == 'https'


def parse_phone(phone):
    """
    The problem: parsing an American phone number. The client wanted to be able to enter the number free-form
    (in a single field), but then wanted to store the area code, trunk, number, and optionally an extension separately
    in the company’s database.

    Examples:
    Here are the phone numbers I needed to be able to accept:

    800-555-1212
    800 555 1212
    800.555.1212
    (800) 555-1212
    1-800-555-1212
    800-555-1212-1234
    800-555-1212x1234
    800-555-1212 ext. 1234
    work 1-(800) 555.1212 #1234

    :param phone:
    :return: a tuple containing the area code, trunk, number and optionally an extension
    """
    phonePattern = re.compile('''
                # don't match beginning of string, number can start anywhere
    (\d{3})     # area code is 3 digits (e.g. '800')
    \D*         # optional separator is any number of non-digits
    (\d{3})     # trunk is 3 digits (e.g. '555')
    \D*         # optional separator
    (\d{4})     # rest of number is 4 digits (e.g. '1212')
    \D*         # optional separator
    (\d*)       # extension is optional and can be any number of digits
    $           # end of string
    ''', re.VERBOSE)
    res = phonePattern.search(phone)
    return [match for match in res.groups() if match != ''] if res is not None else None


def logger(func):
    """Logger in console for function arguments
    Notice our inner function takes any arbitrary number and type of parameters at point #1 and passes them along
    as arguments to the wrapped function at point #2. This allows us to wrap or decorate any function,
    no matter it's signature."""

    @functools.wraps(func)
    def decorator(*args, **kwargs):  # 1

        print("Arguments were: %s, %s" % (args, kwargs))
        return func(*args, **kwargs)  # 2

    return decorator


def time_monotonic(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        end = time.monotonic()

        print(time.ctime(), 'start : {:>9.2f}'.format(start))
        print(time.ctime(), 'end   : {:>9.2f}'.format(end))
        print(time.ctime(), 'span  : {:>9.2f}'.format(end - start))

        return result

    return inner


def generate_password_hash(password):
    """
    Generates a hashed password using pbkdf2_sha512 algorithm

    :param password: The sha512 password from login form or api request
    :return: A sha512 -> pbkdf2_sha512 encrypted password
    """
    return pbkdf2_sha512.hash(password)


def check_password_hash(password, hash):
    """
    Checks the password sent by user in the request matches the one in database
    The password in database is encrypted more than the one in the request at this stage
    :param password: sha512-hashed password
    :param hash: pbkdf2_sha512 encrypted password
    :return: True if passwords match, False otherwise
    """
    return pbkdf2_sha512.verify(password, hash)
