# Repository for Users - handles basic database queries and actions on the User model
# Focuses solely on DB access operations (business logic is handled by the services)

from models import db, User


class UserRepository:
    def get_by_id(self, user_id):
        # Retrieve a user by their ID
        return User.query.get(user_id)

    def get_by_username(self, username):
        # Retrieve a user by username (used during login authentication)
        return User.query.filter_by(username=username).first()

    def get_by_email(self, email):
        # Retrieve a user by email (used to enforce uniqueness during registration)
        return User.query.filter_by(email=email).first()

    def get_all(self):
        # Retrieve all users (used in the administrative panel)
        return User.query.all()

    def add(self, user):
        # Add a user to the database session (without committing the transaction)
        db.session.add(user)

    def delete(self, user):
        # Mark a user for deletion in the database session (without committing)
        db.session.delete(user)
