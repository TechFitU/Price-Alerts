# -*- coding: utf-8 -*-

"""
resources/models.py

Module that contains api resources regarding stores information management.
"""
from flask_jwt_extended import jwt_required, get_jwt_claims, get_jwt_identity, jwt_optional, fresh_jwt_required
from flask_restful import Resource, abort

from models.store import StoreModel


class StoreResource(Resource):
    @jwt_required
    def get(self, name):
        """Endpoint that returns a store by its name. Required JWT authenticated user before proceed with the request
        This is using docstrings for specifications.
        ---
        tags:
          - Stores
        parameters:
          - in: path
            name: name
            required: true
            description: The name of the store
            type: string
        responses:
          200:
            description: The store object
            id: Store
            schema:
              $ref: '#/definitions/Store'
        """
        store = self.get_or_404(name)
        return store.json()

    @fresh_jwt_required
    def post(self, name):
        """This endpoint allows to create a store
        Requires a fresh jwt token. # Only fresh JWTs can access this endpoint
        ---
        tags:
          - Stores
        definitions:
          Store:
            id:
              type: integer
              description: Identifier of the store
            name:
              type: string
              description: Name of the store
            items:
              type: array
              items:
                $ref: '#/definitions/Item'
        parameters:
          - in: path
            name: name
            required: true
            description: The name of the store!
            type: string
        responses:
          201:
            description: The store has been created
            schema:
              $ref: '#/definitions/Store'
          401:
            description: User not logged in
        """
        if StoreModel.find_by_name(name):
            return {
                       'message':
                           "A store with name '{}' already exists.".format(name)
                   }, 400

        store = StoreModel(name)
        try:
            store.save_to_db()
        except:
            return {"message": "An error occurred creating the store."}, 500

        return store.json(), 201

    @fresh_jwt_required
    def delete(self, name):
        """This endpoint is used to delete a store.
        Requires a fresh jwt to execute the request.
        ---
        tags:
          - Stores
        parameters:
          - in: path
            name: name
            required: true
            description: The name of the store, try store1!
            type: string
        responses:
          200:
            description: Store deleted
          401:
            description: Authorization required
          403:
            description: Admin privilege required

        """

        # Checking claims for actually execute or not the request as expected
        claims = get_jwt_claims()
        if not claims['is_admin']:
            return {'message': 'Admin privilege required'}, 403

        store = StoreModel.find_by_name(name)
        if store:
            store.delete_from_db()
        return {'message': 'Store deleted'}, 200

    def get_or_404(self, name):
        store = StoreModel.find_by_name(name)
        if store is None:
            abort(404, message="Store not found".format(name))
        else:
            return store

    def check_exists_400(self, name):
        store = StoreModel.find_by_name(name)
        if store:
            abort(
                400,
                message="A store with name '{}' already exists.".format(name))


class StoreListResource(Resource):
    @jwt_optional
    def get(self):
        """
        Returns the list of stores
        ---
        tags:
          - Stores
        definitions:
          Store:
            type: object
            properties:
              id:
                type: integer
                description: Identifier of the store
                default: 1
              name:
                type: string
                description: Name of the Store
                default: New Store
              items:
                type: array
                items:
                  $ref: '#/definitions/Item'

          Item:
            type: object
            properties:
              id:
                type: integer
                description: Identifier of the Item
              name:
                type: string
                description: Name of the item
              store_id:
                type: integer


        responses:
          200:
            description: The list of stores data
            schema:
              id: Stores
              type: object
              properties:
                stores:
                  type: array
                  items:
                    $ref: '#/definitions/Store'
            examples:
              stores: [{'id': 1, 'name': 'New Store', 'items': []},]
        """

        # Access the identity of the current user identity (username) with get_jwt_identity
        current_user = get_jwt_identity()
        stores = [store.json() for store in StoreModel.find_all()]
        if current_user:
            return {'stores': stores}

        return {
            'stores': list(map(lambda x: x['name'], stores)),
            'message': 'More data available if logged in'
        }
