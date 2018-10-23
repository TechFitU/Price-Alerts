# -*- coding: utf-8 -*-
"""
StoreTest

Only test methods that don't depend on databases or other classes of your app
"""
import unittest

from pricealerts.models import StoreModel
from tests.unit.unit_base_test import UnitBaseTest


class StoreTest(UnitBaseTest):
    def test_create_store(self):
        store = StoreModel(name='store1', url_prefix='http://johnlewis.com', tag_name='span',
                           query_string={'id':'priceblock_ourprice'})
        self.assertEqual('store1', store.name)
        self.assertEqual('http://johnlewis.com', store.url_prefix)
        self.assertEqual('span', store.tag_name)
        self.assertEqual('{"id": "priceblock_ourprice"}', store.query_string)

if __name__ == '__main__':
    unittest.main()