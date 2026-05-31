# Authentication Service - handles registration, login, token refresh, and logout
# Decoupled from the HTTP layer; only works with inputs and returns dicts.

from datetime import datetime, timedelta
import secrets
from flask_jwt_extended import create_access_token
from models import User, RefreshToken, UserStats, db


class AuthService:
    # Receives repository instances via constructor injection
    def __init__(self, user_repo, token_repo, stats_repo):
        self.user_repo = user_repo    # users table
        self.token_repo = token_repo  # refresh_tokens table
        self.stats_repo = stats_repo  # initialize user stats on registration

    def register(self, username, email, password):
        # Verify uniqueness of username and email, create user, issue token pair
        if self.user_repo.get_by_username(username):
            return {'error': 'Username already exists'}, 400
        if self.user_repo.get_by_email(email):
            return {'error': 'Email already exists'}, 400

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        self.user_repo.add(new_user)
        db.session.flush()  # flush to get the auto-incremented user ID

        # Create an empty stats record for the new user
        user_stats = UserStats(user_id=new_user.id)
        self.stats_repo.add_stats(user_stats)
        db.session.commit()

        access_token = create_access_token(identity=str(new_user.id))
        refresh_token = secrets.token_hex(32)  # 64-char random hex string

        # Persist the refresh token with a 7-day TTL
        new_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=new_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.token_repo.add(new_refresh_token)
        db.session.commit()

        return {
            'message': 'User registered successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': new_user.to_dict()
        }, 201

    def login(self, username, password):
        # Validate credentials and return a new token pair
        user = self.user_repo.get_by_username(username)
        if not user or not user.check_password(password):
            # Generic message to prevent username enumeration
            return {'error': 'Invalid username or password'}, 401

        access_token = create_access_token(identity=str(user.id))
        refresh_token = secrets.token_hex(32)

        new_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.token_repo.add(new_refresh_token)
        db.session.commit()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }, 200

    def refresh(self, refresh_token):
        # Token rotation: validate the old refresh token, issue a new pair
        if not refresh_token:
            return {'error': 'Refresh token missing'}, 400

        token_entry = self.token_repo.get_valid_token(refresh_token)
        if not token_entry:
            return {'error': 'Invalid refresh token'}, 401

        if token_entry.expires_at < datetime.utcnow():
            return {'error': 'Refresh token expired'}, 401

        # Revoke the old token and issue a new one (enforces secure rotation)
        new_refresh_token_str = secrets.token_hex(32)
        token_entry.revoked = True

        new_token_entry = RefreshToken(
            token=new_refresh_token_str,
            user_id=token_entry.user_id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.token_repo.add(new_token_entry)
        db.session.commit()

        access_token = create_access_token(identity=str(token_entry.user_id))

        return {
            'access_token': access_token,
            'refresh_token': new_refresh_token_str
        }, 200

    def logout(self, refresh_token):
        # Mark the refresh token as revoked so it can't be reused
        if refresh_token:
            token_entry = self.token_repo.get_token(refresh_token)
            if token_entry:
                token_entry.revoked = True
                db.session.commit()
        return {'message': 'Logged out successfully'}, 200

    def delete_user(self, user_id):
        # Delete the account; cascades to all user decks and cards
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        self.user_repo.delete(user)
        db.session.commit()
        return {'message': 'User deleted successfully'}, 200
