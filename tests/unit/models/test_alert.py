# -*- coding: utf-8 -*-
"""
AlertTest

Only test methods that don't depend on databases or other classes of your app
"""
import unittest

from pricealerts.models import AlertModel, UserModel
from tests.unit.unit_base_test import UnitBaseTest


class AlertTest(UnitBaseTest):
    def setUp(self):
        super(AlertTest, self).setUp()

        self.alert = AlertModel(price_limit=20, item_id=1, user_id=1,
                 active=True, shared=False, contact_phone='210-435-2345', contact_email='alex@uci.cu',
                 last_checked=None, check_every=10)
    def test_create_alert(self):

        self.assertEqual(20, self.alert.price_limit)
        self.assertEqual(1, self.alert.item_id)
        self.assertEqual(1, self.alert.user_id)
        self.assertEqual(True, self.alert.active)
        self.assertEqual(False, self.alert.shared)
        self.assertEqual('210-435-2345', self.alert.contact_phone)
        self.assertEqual('alex@uci.cu', self.alert.contact_email)
        self.assertEqual(10, self.alert.check_every)
        self.assertEqual(None, self.alert.last_checked)


if __name__ == '__main__':
    unittest.main()
    import doctest

    doctest.testmod()