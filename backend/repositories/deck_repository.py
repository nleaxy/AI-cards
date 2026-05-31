# Repository for Decks - handles retrieval, creation, deletion, sorting, and pagination

from models import db, Deck, Card
from sqlalchemy import func
from datetime import datetime


class DeckRepository:
    def get_by_id(self, deck_id):
        # Retrieve a deck by its ID
        return Deck.query.get(deck_id)

    def get_user_decks(self, user_id, sort_by='newest', page=1, per_page=10,
                       search=None, min_cards=None, max_cards=None,
                       date_from=None, date_to=None):
        # Base query filtering by user_id
        query = Deck.query.filter_by(user_id=user_id)

        # Text filter: searches within title and description (case-insensitive ILIKE)
        if search:
            pattern = f'%{search}%'
            query = query.filter(
                db.or_(Deck.title.ilike(pattern), Deck.description.ilike(pattern))
            )

        # Filter by creation date range
        if date_from:
            try:
                dt_from = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Deck.created_at >= dt_from)
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.strptime(date_to, '%Y-%m-%d')
                # Include the entire final day (up to the next midnight)
                from datetime import timedelta
                query = query.filter(Deck.created_at < dt_to + timedelta(days=1))
            except ValueError:
                pass

        # Filter by card count (requires a subquery to aggregate counts)
        if min_cards is not None or max_cards is not None:
            card_count_sub = (db.session.query(
                Card.deck_id,
                func.count(Card.id).label('cnt')
            ).group_by(Card.deck_id).subquery())
            query = query.outerjoin(card_count_sub, Deck.id == card_count_sub.c.deck_id)
            if min_cards is not None:
                query = query.filter(
                    db.or_(card_count_sub.c.cnt >= min_cards, card_count_sub.c.cnt.is_(None) if min_cards == 0 else False)
                )
            if max_cards is not None:
                query = query.filter(
                    db.or_(card_count_sub.c.cnt <= max_cards, card_count_sub.c.cnt.is_(None))
                )

        # Apply the requested ordering
        if sort_by == 'newest':
            query = query.order_by(Deck.created_at.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Deck.created_at.asc())
        elif sort_by == 'name':
            query = query.order_by(Deck.title.asc())
        elif sort_by == 'cards':
            # Order by card count - joins with the cards table
            query = query.outerjoin(Card, Deck.id == Card.deck_id).group_by(Deck.id).order_by(func.count(Card.id).desc())

        # Return a Flask-SQLAlchemy Pagination object instead of a raw list
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def add(self, deck):
        # Add a deck to the database session
        db.session.add(deck)

    def delete(self, deck):
        # Delete the deck (cascades to all associated cards)
        db.session.delete(deck)
