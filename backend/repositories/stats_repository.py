# репозиторий для статистики - работа с таблицами user_stats и study_sessions

from models import db, UserStats, StudySession


class StatsRepository:
    def get_by_user_id(self, user_id):
        # возвращаем статистику для конкретного пользователя
        return UserStats.query.filter_by(user_id=user_id).first()

    def add_stats(self, stats):
        # добавляем новую запись статистики (создается при регистрации пользователя)
        db.session.add(stats)

    def add_session(self, session):
        # сохраняем результаты конкретной учебной сессии
        db.session.add(session)
