# сервис для работы со статистикой - подсчет стриков, сохранение учебных сессий

from models import db, UserStats, StudySession, Deck, Card
from datetime import datetime


class StatsService:
    # получает репозитории через конструктор - dependency injection
    def __init__(self, stats_repo, deck_repo, card_repo, user_repo):
        self.stats_repo = stats_repo  # для работы со статистикой
        self.deck_repo = deck_repo    # чтобы обновить дату последнего изучения колоды
        self.card_repo = card_repo    # чтобы обновить статистику по каждой карточке
        self.user_repo = user_repo    # для поиска пользователя

    def create_session(self, user_id, data):
        # сохраняем результаты учебной сессии и обновляем всю статистику
        session = StudySession(
            user_id=user_id,
            deck_id=data['deck_id'],
            cards_studied=data['cards_studied'],    # сколько карточек показали
            cards_correct=data['cards_correct'],    # сколько ответили правильно
            duration_seconds=data.get('duration_seconds', 0)
        )

        # ищем статистику пользователя или создаем если не существует
        user_stats = self.stats_repo.get_by_user_id(user_id)
        if not user_stats:
            user_stats = UserStats(user_id=user_id)
            self.stats_repo.add_stats(user_stats)
            db.session.flush()

        # обрабатываем результат каждой карточки
        for card_result in data.get('card_results', []):
            card = self.card_repo.get_by_id(card_result['card_id'])
            if card:
                card.times_studied += 1
                card.last_studied = datetime.utcnow()

                if card_result['correct']:
                    card.times_correct += 1
                    # добавляем карточку в список уникально изученных
                    user_stats.add_unique_card(card.id)
                    # увеличиваем стрик (серию правильных ответов)
                    user_stats.increment_streak(card.id)
                else:
                    # сбрасываем стрик при неправильном ответе
                    user_stats.reset_streak()

        # обновляем дату последнего изучения у колоды
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
        # возвращаем статистику пользователя, создаем запись если её еще нет
        user_stats = self.stats_repo.get_by_user_id(user_id)
        if not user_stats:
            user_stats = UserStats(user_id=user_id)
            self.stats_repo.add_stats(user_stats)
            db.session.commit()
        return user_stats.to_dict(), 200

    def reset_stats(self, user_id):
        # обнуляем всю статистику пользователя (колоды и карточки не трогаем)
        user_stats = self.stats_repo.get_by_user_id(user_id)
        if user_stats:
            user_stats.reset_stats()
            db.session.commit()
            return {'message': 'Статистика сброшена', 'stats': user_stats.to_dict()}, 200
        return {'error': 'Статистика не найдена'}, 404
