# Repository for statistics - interacts with user_stats and study_sessions tables

from models import db, UserStats, StudySession


class StatsRepository:
    def get_by_user_id(self, user_id):
        # Retrieve statistics records for a specific user ID
        return UserStats.query.filter_by(user_id=user_id).first()

    def add_stats(self, stats):
        # Add a new user statistics record (initialized during registration)
        db.session.add(stats)

    def add_session(self, session):
        # Save study session records
        db.session.add(session)
