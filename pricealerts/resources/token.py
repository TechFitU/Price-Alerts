# -*- coding: utf-8 -*-
from flask import jsonify, current_app
from flask_jwt_extended import (jwt_required, create_access_token, get_current_user, set_access_cookies, \
                                jwt_refresh_token_required, get_jwt_identity, get_csrf_token, get_jwt_claims,
                                fresh_jwt_required)
from flask_restful import Resource

from utils.blacklist_helpers import add_token_to_database, get_user_tokens, prune_database


class TokenRefresh(Resource):
    """Api resource that enables to refresh access tokens
    A revoked refresh tokens will not be able to access this endpoint.
    Refresh tokens cannot access an endpoint that is protected with jwt_required() and access tokens
    cannot access an endpoint that is protected with jwt_refresh_token_required().
    """

    @jwt_refresh_token_required
    def post(self):
        """Refresh token endpoint.
        Get a new access token without requiring username and password—only the 'refresh token'
        provided in the /login endpoint. This will generate a new access token from the refresh token,
        but will mark that access token as non-fresh, as we do not actually verify a password in this endpoint.
        Note that refreshed access tokens have a `fresh=False`, which means that the user may have not
        given us their username and password for potentially a long time (if the token has been
        refreshed many times over).

        ---
        tags:
          - Auth
        responses:
          200:
            description: The refreshed token
        """
        current_user = get_current_user()

        # Create the new access token and save it to database
        new_access_token = create_access_token(
            identity=current_user, fresh=False)
        add_token_to_database(new_access_token,
                              current_app.config['JWT_IDENTITY_CLAIM'])

        raw_response = {'refresh': True, 'access_token': new_access_token}

        if not current_app.config['JWT_CSRF_IN_COOKIES']:
            # Return the double submit values in the resulting JSON
            # instead of in additional cookies
            raw_response.update({
                'access_csrf':
                    get_csrf_token(new_access_token)
            })

        # Create the response object
        resp = jsonify(raw_response)
        resp.status_code = 200
        # This header is used for Swagger-UI, it uses this header to authenticate the following requests.
        resp.headers.extend({'jwt-token': new_access_token})
        resp.headers.extend({'access_csrf': get_csrf_token(new_access_token)})

        # Set the JWT access cookie in the response (useful for browser apps only)
        # We need to call these functions to set the JWTs in the httpOnly cookies
        set_access_cookies(resp, new_access_token)

        return resp


class TokenList(Resource):
    """Api resource that enables to see the JWT for a user

    """

    @jwt_required
    def get(self):
        """
        Returns the list of tokens for the current user
        ---
        tags:
          - Auth
        responses:
          200:
            description: The list of tokens for the current logged user.
        """
        user_identity = get_jwt_identity()
        all_tokens = get_user_tokens(user_identity)
        ret = [token.json() for token in all_tokens]
        return jsonify(ret)

    @fresh_jwt_required
    def delete(self):
        """Endpoint to delete all the tokens that are revoked and expired
        Requires a fresh jwt token. Only fresh JWTs can access this endpoint
        ---
        tags:
          - Auth
        responses:
          200:
            description: Expired tokens deleted
          401:
            description: Authorization required
          403:
            description: Admin privilege required
        """
        # Checking claims for actually execute or not the request as expected
        claims = get_jwt_claims()
        if not claims['is_admin']:
            return {'message': 'Admin privilege required'}, 403

        prune_database()
        return jsonify({'message': 'Expired tokens deleted'})
