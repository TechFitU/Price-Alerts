# -*- coding: utf-8 -*-
"""
UserTest

Only test methods that don't depend on databases or other classes of your app
"""
import os
import unittest

from werkzeug.security import check_password_hash

from pricealerts.models import UserModel
from tests.unit.unit_base_test import UnitBaseTest
#from pricealerts.utils.helpers import check_password_hash


class UserTest(UnitBaseTest):
    def setUp(self):
        self.api_key = os.urandom(16)
        self.user = UserModel('Alexander', 'alexmtnezf', '12345', phone="800-555-1212",
                              is_admin=True, api_key=self.api_key)

    def test_create_user(self):
        self.assertEqual('800-555-1212', self.user.phone)
        self.assertEqual('alexmtnezf', self.user.username)
        self.assertEqual('Alexander', self.user.name)
        self.assertTrue(self.user.is_admin)
        self.assertFalse(self.user.is_staff)
        assert check_password_hash(self.user.password, '12345')
        self.assertEqual(self.api_key, self.user.api_key)
        self.assertListEqual([], self.user.roles)
        self.assertIsNone(self.user.last_login)

    def test_json(self):
        self.assertDictEqual({
            'id': None,
            'username': 'alexmtnezf',
            'name': 'Alexander',
            'is_admin': True,
            'is_staff': False,
            'phone': "800-555-1212",
            'last_login': None,
            'theme': None

        }, self.user.json())


    def test_user_representation(self):
        self.assertEqual("User(id='None')", str(self.user))

if __name__ == '__main__':
    unittest.main()