# -*- coding: utf-8 -*-
"""
AlertTest class
Class tested: AlertModel

Only test methods that depends on databases or work with other classes and methods of your app
"""
import datetime
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

        self.last_checked = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        self.alert = AlertModel(price_limit=20, item_id=1, user_id=1,
                 active=True, shared=False, contact_phone=None, contact_email='alex@uci.cu',
                 last_checked=self.last_checked, check_every=10)

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
            'price_limit': 20.0,
            'last_checked': self.last_checked,
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

    def test_find_needing_update_with_one_alert(self):
        with self.app_context():
            self.user.save_to_db()
            self.store.save_to_db()
            self.item.save_to_db()
            self.alert.save_to_db()
            print(self.last_checked)

            self.assertEqual(1, len(AlertModel.find_needing_update()))

    def test_find_needing_update_without_alerts(self):
        with self.app_context():
            self.user.save_to_db()
            self.store.save_to_db()
            self.item.save_to_db()
            self.alert.last_checked = self.alert.last_checked + datetime.timedelta(minutes=8)
            self.alert.save_to_db()
            self.assertEqual(0, len(AlertModel.find_needing_update()))

    def test_load_price_change(self):
        with self.app_context():

            with patch('pricealerts.models.ItemModel.load_item_data',
                       return_value = ('Item1',6.00, None)) as mocked_load_item_data:
                self.user.save_to_db()
                self.store.save_to_db()
                self.item.save_to_db()
                self.alert.save_to_db()
                self.assertEqual('Item1', self.alert.item.name)
                self.assertEqual(19.99, self.alert.item.price)
                self.assertEqual(None, self.alert.item.image)


                self.alert.load_price_change()
                mocked_load_item_data.assert_called_once()
                self.assertEqual('Item1', self.alert.item.name)
                self.assertEqual(6.0, self.alert.item.price)
                self.assertEqual(None, self.alert.item.image)
                self.assertAlmostEqual(self.alert.last_checked,datetime.datetime.utcnow(), delta=datetime.timedelta(seconds=10))
