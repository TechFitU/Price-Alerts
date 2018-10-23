# -*- coding: utf-8 -*-
"""
StoreTest
Class tested: StoreModel

Only test methods that depends on databases or work with other classes and methods of your app
"""
import os

from mock import patch, Mock
from sqlalchemy.exc import OperationalError
from werkzeug.security import check_password_hash

from pricealerts import db
from pricealerts.common.base_model import DatabaseError
from pricealerts.models import UserModel, RegisterUserError, IncorrectPasswordError, UserNotFoundError
from tests.base_test import BaseTest


class UserTest(BaseTest):
    def setUp(self):
        super(UserTest, self).setUp()
        self.user = UserModel('Alex', 'alexmtnezf@gmail.com', '12345', is_admin=True)

    def test_crud(self):
        with self.app_context():

            self.assertIsNone(UserModel.find_by_name('Alex'))
            self.assertIsNone(UserModel.find_by_username('alexmtnezf'))
            self.assertIsNone(UserModel.find_by_id(1))

            self.user.save_to_db()
            self.assertIsNotNone(UserModel.find_by_name('Alex'))
            self.user.username = 'pepito'
            self.user.save_to_db()
            self.assertIsNone(UserModel.find_by_username('alexmtnezf'))
            self.assertIsNotNone(UserModel.find_by_username('pepito'))

            self.user.delete_from_db()
            self.assertIsNone(UserModel.find_by_name('Alex'))
            self.assertIsNone(UserModel.find_by_username('alexmtnezf'))
            self.assertIsNone(UserModel.find_by_id(1))

    def test_set_password(self):
        self.user.set_password('12345')
        self.assertTrue(check_password_hash(self.user.password, '12345'))

    def test_register_ok(self):
        with self.app_context():
            UserModel.register('alexmtnezf@gmail.com','12345','Alex',"800-555-1212")
            self.assertEqual(1, len(UserModel.find_all()))

    def test_login_valid_true(self):
        with self.app_context():
            self.user.save_to_db()
            self.assertTrue(UserModel.login_valid(email='alexmtnezf@gmail.com', password='12345'))

    def test_login_valid_incorrect_user(self):
        with self.app_context():
            with patch('pricealerts.common.base_model.BaseModel.find_one', return_value=None) as mocked_find_one:
                with self.assertRaises(UserNotFoundError):
                    UserModel.login_valid( email='alexmtnezf@gffil.com', password='12345')
                    mocked_find_one.assert_called_once_with('alexmtnezf@gffil.com')

    def test_login_valid_incorrect_password(self):
        with self.app_context():
            with patch('pricealerts.common.base_model.BaseModel.find_one', return_value=self.user) as mocked_find_one:
                self.assertRaises(IncorrectPasswordError, UserModel.login_valid,
                                  email='alexmtnezf@gmail.com', password='holaaa')
                mocked_find_one.assert_called_once_with(username='alexmtnezf@gmail.com')

    def test_find_by_username_ok(self):
        with self.app_context():
            self.user.save_to_db()
            self.assertEqual('Alex', UserModel.find_by_username('alexmtnezf@gmail.com').name)


    def test_find_by_username_raises_exceptions(self):
        with self.app_context():
            db.drop_all()
            with patch('pricealerts.models.UserModel.query.filter_by') as mocked_filter_by:
                mocked_filter_by.side_effect = DatabaseError('Database not found error')

                with self.assertRaises(DatabaseError):
                    UserModel.find_by_username('alexmtnezf@gmail.com')
                    mocked_filter_by.assert_called_with(username='alexmtnezf@gmail.com')

