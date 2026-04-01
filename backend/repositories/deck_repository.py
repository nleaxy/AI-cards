# репозиторий для колод - поиск, создание, удаление, сортировка и постраничность

from models import db, Deck, Card
from sqlalchemy import func


class DeckRepository:
    def get_by_id(self, deck_id):
        # ищем колоду по id
        return Deck.query.get(deck_id)

    def get_user_decks(self, user_id, sort_by='newest', page=1, per_page=10):
        # возвращаем колоды пользователя с сортировкой и постраничной разбивкой
        query = Deck.query.filter_by(user_id=user_id)

        # применяем нужную сортировку
        if sort_by == 'newest':
            query = query.order_by(Deck.created_at.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Deck.created_at.asc())
        elif sort_by == 'name':
            query = query.order_by(Deck.title.asc())
        elif sort_by == 'cards':
            # сортируем по количеству карточек - нужен join с таблицей cards
            query = query.outerjoin(Card).group_by(Deck.id).order_by(func.count(Card.id).desc())

        # возвращаем объект постраничной разбивки (не просто список)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def add(self, deck):
        # добавляем колоду в сессию бд
        db.session.add(deck)

    def delete(self, deck):
        # помечаем колоду для удаления (все карточки удалятся каскадом)
        db.session.delete(deck)
