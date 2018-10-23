# -*- coding: utf-8 -*-
import datetime

import psycopg2
import sqlalchemy
from flask_login import current_user
from flask.globals import current_app
from sqlalchemy.exc import SQLAlchemyError, StatementError, OperationalError, DBAPIError

from pricealerts.db import db
from pricealerts.utils.helpers import time_monotonic

class DatabaseError(Exception):
    def __init__(self, message):
        self.message = message

class BaseModel(object):
    created = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.datetime.utcnow())
    updated = db.Column(db.DateTime(timezone=False), nullable=True)
    created_by = db.Column(db.String(80), nullable=False, default='system')
    updated_by = db.Column(db.String(80), nullable=True)

    # Instance methods

    def __before_commit_insert__(self):
        """Do Stuff, this will execute before each insert on this table"""
        self.created = datetime.datetime.utcnow()
        self.created_by = current_user.username if current_user is not None \
                                                   and hasattr(current_user, 'username') else 'system'

    def __before_commit_update__(self):
        """Do Stuff, this will execute before each update on this table"""
        self.updated = datetime.datetime.utcnow()
        self.updated_by = current_user.username if current_user is not None \
                                                   and hasattr(current_user, 'username') else 'system'

    def __before_commit_delete__(self):
        """Do Stuff, this will execute before each delete on this table"""
        pass

    def __commit_insert__(self):
        """Do Stuff, this will execute after each insert on this table"""
        pass

    def __commit_update__(self):
        """Do Stuff, this will execute after each update on this table"""
        pass

    def __commit_delete__(self):
        """Do Stuff, this will execute after each update on this table"""
        pass


    def json(self):
        raise NotImplementedError()

    #@time_monotonic
    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
        except OperationalError as ex:
            current_app.logger.error('Data was not saved. SQL executed: {} \nError: {}'.format(ex.statement, str(ex)))
            raise DatabaseError('Data was not saved.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error(
                'Data was not saved. SQL executed: {} \nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Data was not saved.')

        return self

    #@time_monotonic
    def delete_from_db(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except OperationalError as ex:
            current_app.logger.error('Data was not deleted. SQL executed: {} \nError: {}'.format(ex.statement, str(ex)))
            raise DatabaseError('Data was not deleted.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error(
                'Data was not deleted. \nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Data was not deleted.')

        return self

    # Class methods

    @classmethod
    def find_all(cls):
        try:
            return cls.query.all()
        except OperationalError as ex:
            current_app.logger.error('Data was not found. SQL executed: {} \nError: {}'.format(ex.statement,str(ex)))
            raise DatabaseError('Data was not found.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error(
                'Data was not found. \nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Data was not found.')

    @classmethod
    def delete_all(cls):
        '''
        Deletes rows in the database, if possible, otherwise raise an Exception
        Every object in SQLAlchemy is marked as deleted

        :return: Number or deleted rows
        '''
        try:
            num_rows_deleted = db.session.query(cls).delete()
            db.session.commit()
        except OperationalError as ex:
            current_app.logger.error('Data was not deleted. SQL executed: {} \nError: {}'.format(ex.statement, str(ex)))
            raise DatabaseError('Data was not deleted.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error(
                'Data was not deleted. \nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Data was not deleted.')

        return num_rows_deleted

    @classmethod
    #@time_monotonic
    def find_by_name(cls, name):
        try:
            return cls.query.filter_by(name=name).first()
        except OperationalError as ex:
            current_app.logger.error('Data was not found. Error: {}'.format(str(ex)))
            raise DatabaseError('Data was not found.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error('Data was not found. SQL executed: {}\nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Data was not found.')




    @classmethod
    #@time_monotonic
    def find_one(cls, **kwargs):
        try:
            return cls.query.filter_by(**kwargs).first()
        except OperationalError as ex:
            current_app.logger.error('Data was not found. SQL executed: {} \nError: {}'.format(ex.statement,str(ex)))
            raise DatabaseError('Data was not found.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error(
                'Data was not found. \nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Data was not found.')


    @classmethod
    #@time_monotonic
    def find_by_id(cls, _id):
        try:
            return cls.query.get(_id)
        except OperationalError as ex:
            current_app.logger.error('Data was not found. SQL executed: {} \nError: {}'.format(ex.statement, str(ex)))
            raise DatabaseError('Data was not found.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error(
                'Data was not found. \nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Data was not found.')

    @classmethod
    #@time_monotonic
    def find_by(cls, **kwargs):
        try:
            return cls.query.filter_by(**kwargs).all()
        except OperationalError as ex:
            current_app.logger.error('Data was not found. SQL executed: {} \nError: {}'.format(ex.statement, str(ex)))
            raise DatabaseError('Data was not found.')
        except sqlalchemy.exc.DatabaseError as ex:
            current_app.logger.error(
                'Data was not found. \nError: {}'.format(ex.statement, str(ex.orig)))
            raise DatabaseError('Data was not found.')

