# -*- coding: utf-8 -*-
"""
AlertTest class
Class tested: AlertModel

Only test methods that depends on databases or work with other classes and methods of your app
"""
import os

from mock import patch, Mock
from pricealerts import db
from pricealerts.common.base_model import DatabaseError
from pricealerts.models import AlertModel, UserModel, ItemModel, StoreModel
from tests.base_test import BaseTest


class AlertTest(BaseTest):
    def setUp(self):
        super(AlertTest, self).setUp()

        self.store = StoreModel(name='store1', url_prefix='http://johnlewis.com', tag_name='span',
                                query_string={'id': 'priceblock_ourprice'})
        self.user = UserModel('Alex', 'alexmtnezf@gmail.com', '12345', is_admin=True)
        self.item = ItemModel(
            url='https://www.johnlewis.com/john-lewis-partners-amber-clear-swirl-bauble-orange/p3527237',
            price=19.99, name='Item1', store_id=1)

        self.alert = AlertModel(price_limit=20, item_id=1, user_id=1,
                 active=True, shared=False, contact_phone=None, contact_email='alex@uci.cu',
                 last_checked=None, check_every=10)

    def test_alert_representation(self):
        with self.app_context():
            self.user.save_to_db()
            self.store.save_to_db()
            self.item.save_to_db()
            self.alert.save_to_db()
            self.assertEqual("(AlertModel<id=1, user='Alex', item='Item1'>)", str(self.alert))

    def test_json(self):
        expected = {
            'id': 1,
            'price_limit': 20,
            'last_checked': None,
            'check_every': 10.0,
            'item_id': 1,
            'item': 'Item1',
            'user_id': 1,
            'user': 'Alex',
            'active': True,
            'shared': False,
            'contact_phone': None,
            'contact_email': 'alex@uci.cu'
        }
        with self.app_context():
            self.user.save_to_db()
            self.store.save_to_db()
            self.item.save_to_db()
            self.alert.save_to_db()
            self.assertDictEqual(expected, self.alert.json())