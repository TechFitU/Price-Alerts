# -*- coding: utf-8 -*-
"""
ItemTest
Class tested: StoreModel

Only test methods that depends on databases or work with other classes and methods of your app
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
from pricealerts.models import ItemModel, StoreModel, ItemNotLoadedError

from tests.base_test import BaseTest


class ItemTest(BaseTest):

    def setUp(self):
        super(ItemTest, self).setUp()
        self.item = ItemModel(
            url='https://www.johnlewis.com/john-lewis-partners-amber-clear-swirl-bauble-orange/p3527237',
            price=19.99, name='test', store_id=1)


    def test_load_item_data_raises_exception(self):
        mocked_response = MagicMock()
        mocked_response.status_code = 500
        mocked_response.content = 'Some extra data not important'
        with patch('pricealerts.models.requests.get', return_value=mocked_response) as mocked_requests:
            with self.assertRaises(ItemNotLoadedError):
                self.item.load_item_data()
                mocked_requests.assert_called_with(url='https://www.johnlewis.com/john-lewis-partners-amber-clear-swirl-bauble-orange/p3527237')


    def test_load_item_data_correctly(self):
        with self.app_context():
            self.assertTupleEqual(
                ('John Lewis & Partners Amber Clear Swirl Bauble, Orange at John Lewis & Partners', 6.00 ,None),
                              self.item.load_item_data())


if __name__ == '__main__':
    unittest.main()
    import doctest

    doctest.testmod()