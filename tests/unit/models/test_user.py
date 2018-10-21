# -*- coding: utf-8 -*-
"""
UserTest

Only test methods that don't depend on databases or other classes of your app
"""
import os
import unittest

from werkzeug.security import check_password_hash

from pricealerts.models.model import UserModel
from tests.unit.unit_base_test import UnitBaseTest
#from pricealerts.utils.helpers import check_password_hash


class UserTest(UnitBaseTest):
    def test_create_user(self):
        """
        Test the __init__ method of UserModel
        :return:
        """
        api_key = os.urandom(16)
        user = UserModel('Alexander', 'alexmtnezf', '12345', phone="800-555-1212", is_admin=True, api_key=api_key)
        self.assertEqual('800-555-1212', user.phone)
        self.assertEqual('alexmtnezf', user.username)
        self.assertEqual('Alexander', user.name)
        self.assertTrue(user.is_admin)
        assert check_password_hash(user.password, '12345')
        self.assertEqual(api_key, user.api_key)


if __name__ == '__main__':
    unittest.main()