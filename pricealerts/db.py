# -*- coding: utf-8 -*-
import flask

from flask_sqlalchemy import (SQLAlchemy, models_committed, before_models_committed)

db = SQLAlchemy()

recorded = []


@models_committed.connect
def committed(sender, changes):
    """
    This signal is sent before changed common were committed to the database
    The operation is one of 'insert', 'update', and 'delete'.

    :param sender: The sender is the application that emitted the changes.
    :param changes: The receiver is passed the changes parameter with a list of tuples in the form (model instance, operation).
    :return:
    """
    assert flask.signals_available
    assert isinstance(changes, list)
    recorded.extend(changes)

    for obj, change in changes:
        if change == 'insert' and hasattr(obj, '__commit_insert__'):
            obj.__commit_insert__()
        elif change == 'update' and hasattr(obj, '__commit_update__'):
            obj.__commit_update__()
        elif change == 'delete' and hasattr(obj, '__commit_delete__'):
            obj.__commit_delete__()

    #print(changes)


@before_models_committed.connect
def before_committed(sender, changes):
    """
    This signal is sent before changed common were committed to the database
    The operation is one of 'insert', 'update', and 'delete'.

    :param sender: The sender is the application that emitted the changes.
    :param changes: The receiver is passed the changes parameter with a list of tuples in the form (model instance, operation).
    :return:
    """
    assert flask.signals_available
    for obj, change in changes:
        if change == 'insert' and hasattr(obj, '__before_commit_insert__'):
            obj.__before_commit_insert__()
        elif change == 'update' and hasattr(obj, '__before_commit_update__'):
            obj.__before_commit_update__()
        elif change == 'delete' and hasattr(obj, '__before_commit_delete__'):
            obj.__before_commit_delete__()

    #print(changes)
