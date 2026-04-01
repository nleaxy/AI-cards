# репозиторий для карточек - простой crud

from models import db, Card


class CardRepository:
    def get_by_id(self, card_id):
        # ищем карточку по id
        return Card.query.get(card_id)

    def add(self, card):
        # добавляем карточку в сессию бд
        db.session.add(card)

    def delete(self, card):
        # помечаем карточку для удаления
        db.session.delete(card)
