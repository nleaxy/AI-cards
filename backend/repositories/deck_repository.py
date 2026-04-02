# репозиторий для колод - поиск, создание, удаление, сортировка и постраничность

from models import db, Deck, Card
from sqlalchemy import func
from datetime import datetime


class DeckRepository:
    def get_by_id(self, deck_id):
        # ищем колоду по id
        return Deck.query.get(deck_id)

    def get_user_decks(self, user_id, sort_by='newest', page=1, per_page=10,
                       search=None, min_cards=None, max_cards=None,
                       date_from=None, date_to=None):
        # базовый запрос для колод пользователя
        query = Deck.query.filter_by(user_id=user_id)

        # фильтр по тексту: ищем в названии и описании (ILIKE для SQLite)
        if search:
            pattern = f'%{search}%'
            query = query.filter(
                db.or_(Deck.title.ilike(pattern), Deck.description.ilike(pattern))
            )

        # фильтр по диапазону дат создания
        if date_from:
            try:
                dt_from = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Deck.created_at >= dt_from)
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.strptime(date_to, '%Y-%m-%d')
                # включаем весь последний день
                from datetime import timedelta
                query = query.filter(Deck.created_at < dt_to + timedelta(days=1))
            except ValueError:
                pass

        # фильтр по количеству карточек требует подзапроса
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

        # применяем нужную сортировку
        if sort_by == 'newest':
            query = query.order_by(Deck.created_at.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Deck.created_at.asc())
        elif sort_by == 'name':
            query = query.order_by(Deck.title.asc())
        elif sort_by == 'cards':
            # сортируем по количеству карточек - нужен join с таблицей cards
            query = query.outerjoin(Card, Deck.id == Card.deck_id).group_by(Deck.id).order_by(func.count(Card.id).desc())

        # возвращаем объект постраничной разбивки (не просто список)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def add(self, deck):
        # добавляем колоду в сессию бд
        db.session.add(deck)

    def delete(self, deck):
        # помечаем колоду для удаления (все карточки удалятся каскадом)
        db.session.delete(deck)
