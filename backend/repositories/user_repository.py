# репозиторий для работы с пользователями в базе данных
# только простые операции с бд - никакой бизнес-логики здесь нет

from models import db, User


class UserRepository:
    def get_by_id(self, user_id):
        # ищем пользователя по его id в базе данных
        return User.query.get(user_id)

    def get_by_username(self, username):
        # ищем пользователя по имени - используется при входе
        return User.query.filter_by(username=username).first()

    def get_by_email(self, email):
        # ищем пользователя по email - используется при регистрации чтобы проверить уникальность
        return User.query.filter_by(email=email).first()

    def get_all(self):
        # возвращаем всех пользователей - используется в admin panel
        return User.query.all()

    def add(self, user):
        # добавляем пользователя в сессию бд (без commit - сохранения)
        db.session.add(user)

    def delete(self, user):
        # помечаем пользователя для удаления (без commit - сохранения)
        db.session.delete(user)
