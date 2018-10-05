# -*- coding: utf-8 -*-
import logging
import os
import re
import sys
import urllib
import warnings

from six import string_types

logger = logging.getLogger(__name__)

VERSION = '0.1.1'
__author__ = 'alexmtnezf'
__version__ = tuple(VERSION.split('.'))


# return int if possible
def _cast_int(v):
    return int(v) if hasattr(v, 'isdigit') and v.isdigit() else v


def _cast_urlstr(v):
    return urllib.parse.unquote_plus(v) if isinstance(v, str) else v


class NoValue(object):
    def __repr__(self):
        return '<{0}>'.format(self.__class__.__name__)


class Env(object):
    ENVIRON = os.environ
    NOTSET = NoValue()
    BOOLEAN_TRUE_STRINGS = ('true', 'on', 'ok', 'y', 'yes', '1')
    # URL_CLASS = urllib.parse.ParseResult
    DEFAULT_DATABASE_ENV = 'DATABASE_URL'

    def __init__(self, **scheme):
        self.scheme = scheme

    def __call__(self, var, cast=None, default=NOTSET, parse_default=False):
        return self.get_value(
            var, cast=cast, default=default, parse_default=parse_default)

    def __contains__(self, var):
        return var in self.ENVIRON

    def get_value(self, var, cast=None, default=NOTSET, parse_default=False):
        """Return value for given environment variable.

        :param var: Name of variable.
        :param cast: Type to cast return value as.
        :param default: If var not present in environ, return this instead.
        :param parse_default: force to parse default..

        :returns: Value from environment or default (if set)
        """

        logger.debug("get '{0}' casted as '{1}' with default '{2}'".format(
            var, cast, default))

        if var in self.scheme:
            var_info = self.scheme[var]

            try:
                has_default = len(var_info) == 2
            except TypeError:
                has_default = False

            if has_default:
                if not cast:
                    cast = var_info[0]

                if default is self.NOTSET:
                    try:
                        default = var_info[1]
                    except IndexError:
                        pass
            else:
                if not cast:
                    cast = var_info

        try:
            value = self.ENVIRON[var]
        except KeyError:
            if default is self.NOTSET:
                error_msg = "Set the {0} environment variable".format(var)
                raise Exception(error_msg)

            value = default

        # Resolve any proxied values
        if hasattr(value, 'startswith') and value.startswith('$'):
            value = value.lstrip('$')
            value = self.get_value(value, cast=cast, default=default)

        if value != default or (parse_default and value):
            value = self.parse_value(value, cast)

        return value

    # Class and static methods

    @classmethod
    def parse_value(cls, value, cast):
        """Parse and cast provided value

        :param value: Stringed value.
        :param cast: Type to cast return value as.

        :returns: Casted value
        """
        if cast is None:
            return value
        elif cast is bool:
            try:
                value = int(value) != 0
            except ValueError:
                value = value.lower() in cls.BOOLEAN_TRUE_STRINGS
        elif isinstance(cast, list):
            value = list(map(cast[0], [x for x in value.split(',') if x]))
        elif isinstance(cast, tuple):
            val = value.strip('(').strip(')').split(',')
            value = tuple(map(cast[0], [x for x in val if x]))
        elif isinstance(cast, dict):
            key_cast = cast.get('key', str)
            value_cast = cast.get('value', str)
            value_cast_by_key = cast.get('cast', dict())
            value = dict(map(
                lambda kv: (
                    key_cast(kv[0]),
                    cls.parse_value(kv[1], value_cast_by_key.get(kv[0], value_cast))
                ),
                [val.split('=') for val in value.split(';') if val]
            ))
        elif cast is dict:
            value = dict([val.split('=') for val in value.split(',') if val])
        elif cast is list:
            value = [x for x in value.split(',') if x]
        elif cast is tuple:
            val = value.strip('(').strip(')').split(',')
            value = tuple([x for x in val if x])
        elif cast is float:
            # clean string
            float_str = re.sub(r'[^\d,\.]', '', value)
            # split for avoid thousand separator and different locale comma/dot symbol
            parts = re.split(r'[,\.]', float_str)
            if len(parts) == 1:
                float_str = parts[0]
            else:
                float_str = "{0}.{1}".format(''.join(parts[0:-1]), parts[-1])
            value = float(float_str)
        else:
            value = cast(value)
        return value

    @classmethod
    def read_env(cls, env_file=None, **overrides):
        """Read a .env file into os.environ.

        If not given a path to a dotenv path, does filthy magic stack backtracking
        to find manage.py and then find the dotenv.

        http://www.wellfireinteractive.com/blog/easier-12-factor-django/

        https://gist.github.com/bennylope/2999704
        """
        if env_file is None:
            frame = sys._getframe()
            env_file = os.path.join(
                os.path.dirname(frame.f_back.f_code.co_filename), '.env')
            if not os.path.exists(env_file):
                warnings.warn(
                    "%s doesn't exist - if you're not configuring your "
                    "environment separately, create one." % env_file)
                return

        try:
            with open(env_file) if isinstance(env_file,
                                              string_types) else env_file as f:
                content = f.read()
        except IOError:
            warnings.warn("Error reading %s - if you're not configuring your "
                          "environment separately, check this." % env_file)
            return

        logger.debug('Read environment variables from: {0}'.format(env_file))

        for line in content.splitlines():
            m1 = re.match(r'\A([A-Za-z_0-9]+)=(.*)\Z', line)
            if m1:
                key, val = m1.group(1), m1.group(2)
                m2 = re.match(r"\A'(.*)'\Z", val)
                if m2:
                    val = m2.group(1)
                m3 = re.match(r'\A"(.*)"\Z', val)
                if m3:
                    val = re.sub(r'\\(.)', r'\1', m3.group(1))
                cls.ENVIRON.setdefault(key, str(val))

        # set defaults
        for key, value in overrides.items():
            cls.ENVIRON.setdefault(key, value)
