# Repository for Refresh Tokens - manages database operations for RefreshToken models
# Active tokens are stored in the database and can be revoked upon logout or rotation

from models import db, RefreshToken


class TokenRepository:
    def get_valid_token(self, token_str):
        # Retrieve an active (non-revoked) refresh token by its string value
        return RefreshToken.query.filter_by(token=token_str, revoked=False).first()

    def get_token(self, token_str):
        # Retrieve any refresh token by its string value (including revoked ones)
        return RefreshToken.query.filter_by(token=token_str).first()

    def add(self, token):
        # Add a new refresh token to the database session
        db.session.add(token)
