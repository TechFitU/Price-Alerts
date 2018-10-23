# -*- coding: utf-8 -*-
"""
BaseTest

This class should be the parent class to each non-unit test class.
It allows for instantiation of the database dynamically,
and makes sure that it is a new, blank database each time.
"""

from unittest import TestCase

from sqlalchemy.exc import DBAPIError, DatabaseError, OperationalError

from pricealerts import create_app
from pricealerts.db import db


class BaseTest(TestCase):
    # Class variables
    flaskApp = None
    #

    @classmethod
    def setUpClass(cls):
        """
        It runs once and before all the test methods in this class and derived class
        :return: None
        """

        # For PostgreSQL in production: postgresql://user:password@localhost:port/database
        # Configure once the database uri for all tests
        BaseTest.flaskApp = create_app({
            'TESTING':True, # Set my flask app to test mode
            'SQLALCHEMY_DATABASE_URI': 'postgresql://test:1234@localhost:5432/pricealerts_test',
            'SQLALCHEMY_TRACK_MODIFICATIONS': True,
            'PROPAGATE_EXCEPTIONS' : False,
            'SQLALCHEMY_ECHO' : False
        })
        # Set my flask app to test mode
        #BaseTest.flaskApp.testing = True

        # Initialize our database once for every test suite (every test file that contains a BaseTest derived class)
        with cls.flaskApp.app_context():
            # Initialize SQLAlchemy instance
            db.init_app(cls.flaskApp)



    def setUp(self):
        """
        It runs once for every test method in this class and derived classes
        :return: None
        """
        # Make sure your database is created
        with BaseTest.flaskApp.app_context():
            try:
                db.create_all()
            except OperationalError as ex:
                BaseTest.flaskApp.logger.error('Database initialization error . Error: {}'.format(str(ex)))
            except DatabaseError as ex:
                BaseTest.flaskApp.logger.error(
                    'Error in database connection: {}\nError: {}'.format(ex.statement, str(ex)))

        # Get a test client and app context for integration and system tests.
        self.app_context = BaseTest.flaskApp.app_context
        self.client = BaseTest.flaskApp.test_client

    def tearDown(self):
        # Database is blank
        with BaseTest.flaskApp.app_context():
            try:
                db.session.remove()
                db.drop_all()
            except OperationalError as ex:
                BaseTest.flaskApp.logger.error('Database tables drop operation error. Error: {}'.format(str(ex)))
            except DatabaseError as ex:
                BaseTest.flaskApp.logger.error(
                    'Error in database connection: {}\nError: {}'.format(ex.statement, str(ex)))
