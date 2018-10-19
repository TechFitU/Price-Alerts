# -*- coding: utf-8 -*-
import datetime

from flask_login import current_user
from flask.globals import current_app
from pricealerts.db import db
from pricealerts.utils.helpers import time_monotonic


class BaseModel(object):
    created = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.datetime.utcnow())
    updated = db.Column(db.DateTime(timezone=False), nullable=True)
    created_by = db.Column(db.String(80), nullable=True, default='')

    def __before_commit_insert__(self):
        """Do Stuff, this will execute before each insert on this table"""
        self.created = datetime.datetime.utcnow()
        self.created_by = current_user.username if current_user is not None \
                                                   and hasattr(current_user, 'username') else 'None'

    def __before_commit_update__(self):
        """Do Stuff, this will execute before each update on this table"""
        self.updated = datetime.datetime.utcnow()

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

    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def delete_all(cls):
        try:
            num_rows_deleted = db.session.query(cls).delete()
            db.session.commit()
            return {'message': '{} row(s) deleted'.format(num_rows_deleted)}
        except:
            return {'message': 'Something went wrong'}

    @classmethod
    @time_monotonic
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    @time_monotonic
    def find_one(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    @time_monotonic
    def find_by_id(cls, _id):
        return cls.query.get(_id)

    @classmethod
    @time_monotonic
    def find_by(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    def json(self):
        raise NotImplementedError()

    @time_monotonic
    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as ex:
            current_app.logger.error('Data was not saved. Error: {}'.format(str(ex)))
            raise

        return self

    @time_monotonic
    def delete_from_db(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as ex:
            current_app.logger.error('Data was not saved. Error: {}'.format(str(ex)))
            raise
        return self
