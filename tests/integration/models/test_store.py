# -*- coding: utf-8 -*-
"""
StoreTest
Class tested: StoreModel

Only test methods that depends on databases or work with other classes and methods of your app
"""
from pricealerts import db
from pricealerts.common.base_model import DatabaseError
from pricealerts.models import StoreModel, ItemModel, ItemNotFoundError
from tests.base_test import BaseTest


class StoreTest(BaseTest):
    def setUp(self):
        super(StoreTest, self).setUp()
        self.store = StoreModel(name='store1', url_prefix='http://johnlewis.com', tag_name='span',
                           query_string={'id': 'priceblock_ourprice'})

    def test_create_store_empty(self):

        expected = {"id": None, "name": "store1", "items": []}

        self.assertEqual(expected, self.store.json())
        self.assertListEqual([], self.store.items.all())
        self.assertEqual(0, len(self.store.items.all()))

    def test_store_json_with_items(self):
        """
        Tests if json method returns a dic() instance with items list added on it
        :return: None
        """
        with self.app_context():

            self.store.save_to_db()
            ItemModel(name='Item1', url='http://johnlewis.com/item/1', store_id=self.store.id).save_to_db()
            expected = {
                'id': self.store.id,
                'name': 'store1',
                'items': [{
                    "name": "Item1",
                    "price": 0.0,
                    "store_id": self.store.id,
                    'url': 'http://johnlewis.com/item/1'

                }]
            }

            self.assertDictEqual(expected, self.store.json())

    def test_store_json_no_items(self):
        """
        Tests if json method returns a dic() instance of the store,
        with items list empty, and added on it
        :return: None
        """
        with self.app_context():
            expected = {"id": 1, "name": "store1", "items": []}
            self.store.save_to_db()

            self.assertDictEqual(expected, self.store.json())

    def test_crud(self):
        with self.app_context():
            self.assertIsNone(StoreModel.find_by_name('store1'))
            self.store.save_to_db()
            self.assertIsNotNone(StoreModel.find_by_name('store1'))
            self.store.name = 'Amazon'
            self.store.save_to_db()
            self.assertIsNotNone(StoreModel.find_by_name('Amazon'))
            self.store.delete_from_db()
            self.assertIsNone(StoreModel.find_by_name('test'))

    def test_crud_raises_exceptions_in_db_operations(self):
        with self.app_context():
            db.drop_all()

            with self.assertRaises(DatabaseError):
                StoreModel.find_by_name('store1')

            with self.assertRaises(DatabaseError):
                self.store.save_to_db()

    def test_get_item_from_store(self):
        with self.app_context():
            self.store.save_to_db()
            ItemModel(name='Item1', url='http://johnlewis.com/item/1', store_id=self.store.id).save_to_db()
            self.assertEqual('Item1', self.store.get_item(1).name)

    def test_get_item_from_store_not_found(self):
        with self.app_context():
            self.store.save_to_db()
            ItemModel(name='Item1', url='http://johnlewis.com/item/1', store_id=self.store.id).save_to_db()


            # Get an item with id = 2, raises ItemNotFoundError
            self.assertRaises(
                ItemNotFoundError, self.store.get_item, 2)

    def test_delete_item_not_found_from_store(self):

        with self.app_context():

            self.store.save_to_db()
            item = ItemModel(name='Item1', url='http://johnlewis.com/item/1', store_id=self.store.id).save_to_db()  # This item has id = 1
            self.assertEqual(1, item.id)

            # Deleting an item with id = 2, raises ItemNotFoundError
            self.assertRaises(
                ItemNotFoundError, self.store.delete_item, 2)


    def test_delete_item_from_store(self):

        with self.app_context():

            self.store.save_to_db()
            # This item has id = 1, after is saved
            item = ItemModel(name='Item1', url='http://johnlewis.com/item/1', store_id=self.store.id).save_to_db()
            self.assertEqual(1, item.id)

            self.assertEqual(1, self.store.items.count())
            self.store.delete_item(1)
            self.assertEqual(0, self.store.items.count())
