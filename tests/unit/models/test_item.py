# -*- coding: utf-8 -*-
"""
ItemTest

Only test methods that don't depend on databases or other classes of your app
"""
import unittest

from pricealerts.models import ItemModel
from tests.unit.unit_base_test import UnitBaseTest


class ItemTest(UnitBaseTest):
    def setUp(self):
        self.item = ItemModel(url='http://johnlewis.com', price=19.99, name='test', store_id=1)

    def test_create_item(self):

        self.assertEqual('test', self.item.name)
        self.assertEqual(19.99, self.item.price)
        self.assertEqual(1, self.item.store_id)
        self.assertIsNone(self.item.store)
        self.assertEqual('http://johnlewis.com',  self.item.url)

    def test_item_json(self):
        expected = {'name': 'test', 'price': 19.99, 'store_id': 1, 'url':'http://johnlewis.com'}
        self.assertDictEqual(expected, self.item.json())

    def test_item_representation(self):
        self.assertEqual("Item(id='None', name='test')", str(self.item))


if __name__ == '__main__':
    unittest.main()
    import doctest

    doctest.testmod()