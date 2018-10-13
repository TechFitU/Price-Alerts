# -*- coding: utf-8 -*-
"""
ItemTest

Only test methods that don't depend on databases or other classes of your app
"""

from items.models import ItemModel
from tests.unit.unit_base_test import UnitBaseTest


class ItemTest(UnitBaseTest):
    def test_create_item(self):
        """
        Test the __init__ method of ItemModel
        :return: None
        """
        item = ItemModel(price=19.99, name='test', store_id=1)
        self.assertEqual('test', item.name)
        self.assertEqual(19.99, item.price)
        self.assertEqual(1, item.store_id)
        self.assertIsNone(item.store)

    def test_item_json(self):
        """
        Test the json method of ItemModel with all the characteristics of
        :return: None
        """
        item = ItemModel(price=19.99, name='test', store_id=1)
        expected = {'name': 'test', 'price': 19.99, 'store_id': 1}

        self.assertDictEqual(expected, item.json())
