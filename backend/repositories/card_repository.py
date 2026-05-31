# Repository for Cards - handles basic database operations

from models import db, Card


class CardRepository:
    def get_by_id(self, card_id):
        # Retrieve a card by its ID
        return Card.query.get(card_id)

    def add(self, card):
        # Add a card to the database session
        db.session.add(card)

    def delete(self, card):
        # Delete a card from the database session
        db.session.delete(card)
