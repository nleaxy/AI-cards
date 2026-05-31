# Service for study statistics - tracks streaks and saves study sessions

from models import db, UserStats, StudySession, Deck, Card
from datetime import datetime


class StatsService:
    # Receives repositories via constructor injection (dependency injection)
    def __init__(self, stats_repo, deck_repo, card_repo, user_repo):
        self.stats_repo = stats_repo  # stats CRUD
        self.deck_repo = deck_repo    # update deck's last_studied date
        self.card_repo = card_repo    # update per-card statistics
        self.user_repo = user_repo    # user lookups

    def create_session(self, user_id, data):
        # Save study session results and update all related statistics
        session = StudySession(
            user_id=user_id,
            deck_id=data['deck_id'],
            cards_studied=data['cards_studied'],
            cards_correct=data['cards_correct'],
            duration_seconds=data.get('duration_seconds', 0)
        )

        # Get or create the user stats record
        user_stats = self.stats_repo.get_by_user_id(user_id)
        if not user_stats:
            user_stats = UserStats(user_id=user_id)
            self.stats_repo.add_stats(user_stats)
            db.session.flush()

        # Process each card result
        for card_result in data.get('card_results', []):
            card = self.card_repo.get_by_id(card_result['card_id'])
            if card:
                card.times_studied += 1
                card.last_studied = datetime.utcnow()

                if card_result['correct']:
                    card.times_correct += 1
                    user_stats.add_unique_card(card.id)
                    user_stats.increment_streak(card.id)
                else:
                    # Reset streak on incorrect answer
                    user_stats.reset_streak()

        # Update the deck's last studied timestamp
        deck = self.deck_repo.get_by_id(data['deck_id'])
        if deck:
            deck.last_studied = datetime.utcnow()

        self.stats_repo.add_session(session)
        db.session.commit()

        return {
            **session.to_dict(),
            'user_stats': user_stats.to_dict()
        }, 201

    def get_stats(self, user_id):
        # Return user statistics, creating a fresh record if one doesn't exist yet
        user_stats = self.stats_repo.get_by_user_id(user_id)
        if not user_stats:
            user_stats = UserStats(user_id=user_id)
            self.stats_repo.add_stats(user_stats)
            db.session.commit()
        return user_stats.to_dict(), 200

    def reset_stats(self, user_id):
        # Reset all stats for the user; decks and cards are not affected
        user_stats = self.stats_repo.get_by_user_id(user_id)
        if user_stats:
            user_stats.reset_stats()
            db.session.commit()
            return {'message': 'Статистика сброшена', 'stats': user_stats.to_dict()}, 200
        return {'error': 'Статистика не найдена'}, 404
