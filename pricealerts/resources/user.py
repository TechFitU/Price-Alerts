# -*- coding: utf-8 -*-
"""
Module models.py

Allows the user to register, login,
"""
from exception import TokenNotFound
from flasgger import swag_from
from flask import current_app
from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_claims,
    jwt_refresh_token_required, get_jwt_identity, get_raw_jwt, jwt_optional,
    get_csrf_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies, get_current_user)
from flask_restful import Resource, reqparse, abort
from users.errors import IncorrectPasswordError, UserNotFoundError
from users.models import UserModel
from utils.blacklist_helpers import add_token_to_database, revoke_token
from utils.helpers import parse_phone


class UserResource(Resource):
    """This resource allows to get and delete a user by its identifier
    For testing purposes only, in production should be deactivated
    """

    def _get_or_404(self, username):
        store = UserModel.find_by_username(username)
        if store is None:
            abort(
                404,
                message='User with username {} not found'.format(username))
        else:
            return store

    @jwt_required
    @swag_from('../username_specs.yml', methods=['GET'])
    def get(self, username):
        user = self._get_or_404(username)
        response = {'claims': get_jwt_claims()}
        response.update(user.json())
        return response, 200

    @jwt_required
    def delete(self, username):
        """
        This endpoint deletes a user by its username
        ---
        tags:
          - Users
        parameters:
          - in: path
            name: username
            required: true
            description: The username of the User!
            type: string
        responses:
          responses:
            200:
              description: User deleted
            401:
              description: Authorization required
            403:
              description: Admin privilege required
        """
        # Checking claims for actually execute or not the request as expected
        claims = get_jwt_claims()
        if not claims['is_admin']:
            return {'message': 'Admin privilege required'}, 403

        user = UserModel.find_by_username(username)
        if user:
            user.delete_from_db()
        return {'message': 'User deleted'}

    # @classmethod
    # def get(cls, user_id):
    #     user = cls.find_by_id(user_id)
    #     if not user:
    #         return {'message': 'User with id {} not found'}, 404
    #     return user.json()


class UserRegister(Resource):
    """
    This resources allows users to register (sign up) in a POST request
    """

    # Class variable for parsing the request arguments (no matter the HTTP method, such as POST, GET, PUT)
    parser = reqparse.RequestParser()
    parser.add_argument(
        'name',
        type=str,
        nullable=False,
        required=True,
        help='This name cannot be blank')
    parser.add_argument(
        'username',
        type=str,
        nullable=False,
        required=True,
        help='This username cannot be blank')
    parser.add_argument(
        'password',
        type=str,
        nullable=False,
        required=True,
        help="This password cannot be blank.")

    parser.add_argument(
        'phone',
        type=str,
        nullable=True,
        required=False,
        help="This phone must be a US-based phone.")
    parser.add_argument(
        'is_admin',
        type=bool,
        nullable=False,
        help="This user is/is not admin?.")

    # parser.add_argument('roles', type=list, required=True, nullable=False, help="This ?.")

    @swag_from('../user_register_specs.yml', methods=['POST'])
    def post(self):
        data = UserRegister.parser.parse_args()

        if not data.get('phone', None) is None:
            parsed_phone = parse_phone(data['phone'])
            if parsed_phone is None:
                return {"message": "Invalid phone format for the user"}, 400

            data['phone'] = "-".join(parsed_phone).strip('-')

        if UserModel.find_by_username(data['username']):
            return {"message": "A user with that username already exists"}, 400

        user = UserModel(**data)
        try:
            user.save_to_db()
        except:
            return {"message": "An error occurred creating the user."}, 500

        return {"message": "User created successfully."}, 201


class UserLogin(Resource):
    """
    This resource allows to login a user, using their credentials
    """
    # Class variable for parsing the request arguments (no matter the HTTP method, such as POST, GET, PUT)
    parser = reqparse.RequestParser()
    parser.add_argument(
        'username',
        type=str,
        nullable=False,
        required=False,
        help='This username cannot be blank')
    parser.add_argument(
        'password',
        type=str,
        nullable=False,
        required=False,
        help="This password cannot be blank.")

    def post(self):
        """This endpoint allows a user to login with the right credentials
        Standard login endpoint. Will return a fresh access token and a refresh token
        All following lines until the hyphens is added to description
        the format of the first lines until 3 hyphens will be not yaml compliant
        but everything below the 3 hyphens should be.
        ---
        tags:
          - Auth
        parameters:
          - in: body
            name: body
            schema:
              type: object
              properties:
                username:
                  type: string
                  required: true
                  description: The username of the user
                password:
                  type: string
                  required: true
                  description: The password of the user
        responses:
          201:
            description: User logged in successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  default: User logged in successfully
          401:
            id: message
            description: User not logged in
            schema:
              type: object
              properties:
                message:
                  type: string
                  default: Wrong credentials
          422:
            id: message
            description: Data sent not possible to understand
            schema:
              type: object
              properties:
                message:
                  type: string
                  default: Missing JSON in request
        """
        if not request.is_json:
            response = jsonify({"message": "Missing JSON in request"})
            response.status_code = 400  # Or 422, need to double check
            return response

        data = UserLogin.parser.parse_args()

        try:
            UserModel.login_valid(data['username'], data['password'])
        except (IncorrectPasswordError, UserNotFoundError) as loginEx:
            response = jsonify({'message': loginEx.message})
            response.status_code = 401
            return response

        current_user = UserModel.find_by_username(data['username'])

        # create_access_token supports an optional 'fresh' argument,
        # which marks the token as fresh or non-fresh accordingly.
        # As we just verified their username and password, we are
        # going to mark the token as fresh here.
        access_token = create_access_token(
            identity=current_user, fresh=True)
        refresh_token = create_refresh_token(identity=current_user)

        # Store the tokens in our database with a status non-revoked.
        add_token_to_database(access_token,
                              current_app.config['JWT_IDENTITY_CLAIM'])
        add_token_to_database(refresh_token,
                              current_app.config['JWT_IDENTITY_CLAIM'])

        raw_response = {
            'message': 'Logged in as {}'.format(current_user.username),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': current_user.id,
        }

        # Creating the response
        response = jsonify(raw_response)
        response.status_code = 200

        # This header is used for Swagger-UI, it uses this header to authenticate the following requests.
        # This header is used for Swagger-UI, it uses this header to authenticate the following requests.
        response.headers.extend({'jwt-token': access_token})
        response.headers.extend({'access_csrf': get_csrf_token(access_token)})
        response.headers.extend({'refresh_csrf': get_csrf_token(refresh_token)})

        if not current_app.config['JWT_CSRF_IN_COOKIES']:
            # Return the double submit values in the resulting JSON
            # instead of in additional cookies
            raw_response.update({
                'access_csrf':
                    get_csrf_token(access_token),
                'refresh_csrf':
                    get_csrf_token(refresh_token)
            })

        # Set the JWT cookies in the response
        # We need to call these functions to set the JWTs in the httpOnly cookies, sent through our response object
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)

        return response


class FreshUserLogin(Resource):
    """
    This resource allows to login a user, using their credentials
    """
    # Class variable for parsing the request arguments (no matter the HTTP method, such as POST, GET, PUT)
    parser = reqparse.RequestParser()
    parser.add_argument(
        'username',
        type=str,
        nullable=False,
        required=False,
        help='This username cannot be blank')
    parser.add_argument(
        'password',
        type=str,
        nullable=False,
        required=False,
        help="This password cannot be blank.")

    def post(self):
        """This endpoint allows a user to login with the right credentials
        Standard login endpoint. Will return ONLY a fresh access token
        All following lines until the hyphens is added to description
        the format of the first lines until 3 hyphens will be not yaml compliant
        but everything below the 3 hyphens should be.
        ---
        tags:
          - Auth
        parameters:
          - in: body
            name: body
            schema:
              type: object
              properties:
                username:
                  type: string
                  required: true
                  description: The username of the user
                password:
                  type: string
                  required: true
                  description: The password of the user
        responses:
          201:
            description: User logged in successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  default: User logged in successfully
          401:
            id: message
            description: User not logged in
            schema:
              type: object
              properties:
                message:
                  type: string
                  default: Wrong credentials
          422:
            id: message
            description: Data sent not possible to understand
            schema:
              type: object
              properties:
                message:
                  type: string
                  default: Missing JSON in request
        """
        if not request.is_json:
            response = jsonify({"message": "Missing JSON in request"})
            response.status_code = 400  # Or 422, need to double check
            return response

        data = UserLogin.parser.parse_args()

        try:
            UserModel.login_valid(data['username'], data['password'])
        except (IncorrectPasswordError, UserNotFoundError) as loginEx:
            response = jsonify({'message': loginEx.message})
            response.status_code = 401
            return response

        current_user = UserModel.find_by_username(data['username'])

        # create_access_token supports an optional 'fresh' argument,
        # which marks the token as fresh or non-fresh accordingly.
        # As we just verified their username and password, we are
        # going to mark the token as fresh here.
        access_token = create_access_token(
            identity=current_user, fresh=True)

        # Store the token in our database with a status non-revoked.
        add_token_to_database(access_token,
                              current_app.config['JWT_IDENTITY_CLAIM'])

        raw_response = {
            'message': 'Logged in as {}'.format(current_user.username),
            'access_token': access_token,
            'user_id': current_user.id,
        }

        # Creating the response
        response = jsonify(raw_response)
        response.status_code = 200

        # This header is used for Swagger-UI, it uses this header to authenticate the following requests.
        # This header is used for Swagger-UI, it uses this header to authenticate the following requests.
        response.headers.extend({'jwt-token': access_token})
        response.headers.extend({'access_csrf': get_csrf_token(access_token)})

        # By default, the CSRF double submit values are sent back as additional cookies to the caller.
        # If you prefer, you can disable that, and send them back directly to the caller,
        # returning the double submit values in the resulting JSON, instead of in additional cookies:
        if not current_app.config['JWT_CSRF_IN_COOKIES']:
            # Return the double submit values in the resulting JSON
            # instead of in additional cookies
            raw_response.update({
                'access_csrf':
                    get_csrf_token(access_token)
            })

        # Set the JWT cookies in the response
        # We need to call these functions to set the JWTs in the httpOnly cookies, sent through our response object
        set_access_cookies(response, access_token)
        return response


class AllUsers(Resource):
    """This resource allows to list and delete all users in the database
    For testing purposes only, in production should be deactivated
    """

    @jwt_optional
    def get(self):
        """
        Returns the list of users
        This endpoint will work for both protected and unprotected data.
        If no JWT is sent in with the request, get_jwt_identity() will return None
        For testing purposes only, in production should be deactivated
        ---
        tags:
          - Users
        responses:
          200:
            description: The list of users
            schema:
              type: object
              properties:
                users:
                  type: array
                  items:
                    $ref: '#/definitions/User'
            examples:
              { 'users': [{'id': 1, 'name': 'admin', 'username': 'admin'},]}
        """

        def to_json(x):
            return {
                'id': x.id,
                'username': x.username,
                'name': x.name,
                'is_admin': x.is_admin
            }

        # Access the identity of the JWT (username) with get_jwt_identity
        current_user = get_jwt_identity()
        users = list(map(lambda x: to_json(x), UserModel.find_all()))
        if current_user:
            return {'users': users}

        return {
            'users': [x['name'] for x in users],
            'message': 'More data available if logged in'
        }

    @jwt_required
    def delete(self):
        """DELETE ALL OF USERS
        For testing purposes only, in production should be deactivated
        ---
        tags:
          - Users
        responses:
          200:
            description: Users deleted
        """
        # Checking claims for actually execute or not the request as expected
        claims = get_jwt_claims()

        if 'admin' not in get_current_user().roles:
            return {"message": "Forbidden: Admin privilege required"}, 403

        if not claims['is_admin']:
            return {'message': 'Forbidden: Admin privilege required'}, 403
        return UserModel.delete_all()


# Because the JWTs are stored in an httponly cookie now, we cannot
# log the user out by simply deleting the cookie in the frontend.
# We need the backend to send us a response to delete the cookies
# in order to logout. unset_jwt_cookies is a helper function to
# do just that.
class UserLogoutAccess(Resource):
    @jwt_required
    def delete(self):
        """Logout a user.
        By sending an order to the browser to unset the cookie with the JWTs saved,
        and revoking the current access token.
        Revokes the token based on the token jti property and the user identity
        ---
        tags:
          - Auth
        responses:
          200:
            description: User logged out
        """

        user_identity = get_jwt_identity()
        jti = get_raw_jwt()['jti']
        try:
            revoke_token(jti, user_identity)
        except TokenNotFound:
            resp = jsonify({'message': 'The specified token was not found'})
            resp.status_code = 404
        else:
            resp = jsonify({
                'message': 'Successfully logged out',
                'logout': True
            })
            resp.status_code = 200
            unset_jwt_cookies(resp)

        return resp


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def delete(self):
        """Logout a user.
        By sending an order to the browser to unset the cookie with the JWTs saved,
        and revoking the current refresh token.
        Revokes the access token based on the jti property and the user identity
        ---
        tags:
          - Auth
        responses:
          200:
            description: User logged out
        """

        user_identity = get_jwt_identity()
        jti = get_raw_jwt()['jti']
        try:
            revoke_token(jti, user_identity)
        except TokenNotFound:
            resp = jsonify({'message': 'The specified token was not found'})
            resp.status_code = 404
        else:
            resp = jsonify({
                'message': 'Successfully logged out',
                'logout': True
            })
            resp.status_code = 200
            unset_jwt_cookies(resp)

        return resp
