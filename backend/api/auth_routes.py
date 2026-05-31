# Authentication API routes - handles registration, login, token refresh, logout, and account deletion
# The refresh token is stored in an HttpOnly cookie - JavaScript does not have access to it

from flask import Blueprint, request, jsonify, make_response
from core.container import container
from flask_jwt_extended import jwt_required, get_jwt_identity

# Create a blueprint - acts as a mini-application hosting a group of related routes
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def set_refresh_cookie(response, refresh_token):
    # Set the refresh token in an HttpOnly cookie - the browser will store and send it automatically
    # httponly=True prevents client-side scripts from reading the cookie (mitigates XSS attacks)
    # samesite='Lax' ensures the cookie is only sent on same-site requests (mitigates CSRF attacks)
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,        # inaccessible to client-side JavaScript
        samesite='Lax',       # mitigation for CSRF attacks
        secure=False,         # True in production (HTTPS only), False for local development
        max_age=7 * 24 * 3600  # cookie lifetime (7 days)
    )
    return response


@auth_bp.route('/register', methods=['POST'])
def register():
    # Register a new user - pass incoming request payload to the authentication service
    data = request.json
    result, status_code = container.auth_service.register(
        data.get('username'),
        data.get('email'),
        data.get('password')
    )
    if status_code == 201:
        # Extract the refresh token from response data and store it in the HttpOnly cookie
        refresh_token = result.pop('refresh_token', None)
        response = make_response(jsonify(result), status_code)
        if refresh_token:
            set_refresh_cookie(response, refresh_token)
        return response
    return jsonify(result), status_code


@auth_bp.route('/login', methods=['POST'])
def login():
    # User login - authenticate credentials using the authentication service
    data = request.json
    result, status_code = container.auth_service.login(
        data.get('username'),
        data.get('password')
    )
    if status_code == 200:
        # Extract the refresh token from response data and store it in the HttpOnly cookie
        refresh_token = result.pop('refresh_token', None)
        response = make_response(jsonify(result), status_code)
        if refresh_token:
            set_refresh_cookie(response, refresh_token)
        return response
    return jsonify(result), status_code


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    # Access token refresh - read the refresh token from cookies rather than the request body
    # The browser automatically forwards the cookie with the request
    refresh_token = request.cookies.get('refresh_token')
    result, status_code = container.auth_service.refresh(refresh_token)
    if status_code == 200:
        # Set the new rotated refresh token in the cookie (token rotation)
        new_refresh_token = result.pop('refresh_token', None)
        response = make_response(jsonify(result), status_code)
        if new_refresh_token:
            set_refresh_cookie(response, new_refresh_token)
        return response
    return jsonify(result), status_code


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()  # This route requires a valid access token
def logout():
    # Logout - revoke the refresh token in the database and clear the client cookie
    refresh_token = request.cookies.get('refresh_token')
    result, status_code = container.auth_service.logout(refresh_token)
    response = make_response(jsonify(result), status_code)
    # Remove the HttpOnly cookie from the browser
    response.delete_cookie('refresh_token', samesite='Lax')
    return response


@auth_bp.route('/user', methods=['DELETE'])
@jwt_required()  # Restricted to authenticated users
def delete_user():
    # Account deletion - retrieve user ID from JWT identity and delete via authentication service
    user_id = int(get_jwt_identity())
    result, status_code = container.auth_service.delete_user(user_id)
    response = make_response(jsonify(result), status_code)
    if status_code == 200:
        response.delete_cookie('refresh_token', samesite='Lax')
    return response
