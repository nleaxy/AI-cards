# сервис авторизации - вся логика регистрации, входа и работы с токенами
# сервис не знает про http, он работает только с данными и возвращает результат

from datetime import datetime, timedelta
import secrets
from flask_jwt_extended import create_access_token
from models import User, RefreshToken, UserStats, db


class AuthService:
    # получает репозитории через конструктор - это и есть dependency injection
    def __init__(self, user_repo, token_repo, stats_repo):
        self.user_repo = user_repo    # для работы с таблицей users
        self.token_repo = token_repo  # для работы с таблицей refresh_tokens
        self.stats_repo = stats_repo  # для создания начальной статистики

    def register(self, username, email, password):
        # регистрация: проверяем что логин и email свободны, создаем юзера и выдаем токены
        if self.user_repo.get_by_username(username):
            return {'error': 'Username already exists'}, 400
        if self.user_repo.get_by_email(email):
            return {'error': 'Email already exists'}, 400

        # создаем пользователя и хэшируем пароль (никогда не храним пароль в открытом виде)
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        self.user_repo.add(new_user)
        db.session.flush()  # flush чтобы получить id нового пользователя до commit

        # создаем пустую запись статистики для нового пользователя
        user_stats = UserStats(user_id=new_user.id)
        self.stats_repo.add_stats(user_stats)
        db.session.commit()

        # генерируем access token (jwt) и refresh token (случайная строка)
        access_token = create_access_token(identity=str(new_user.id))
        refresh_token = secrets.token_hex(32)  # 64-символьная случайная строка

        # сохраняем refresh токен в базу с датой истечения
        new_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=new_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.token_repo.add(new_refresh_token)
        db.session.commit()

        return {
            'message': 'User registered successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': new_user.to_dict()
        }, 201

    def login(self, username, password):
        # вход: проверяем пароль и выдаем новую пару токенов
        user = self.user_repo.get_by_username(username)
        if not user or not user.check_password(password):
            # возвращаем одну и ту же ошибку чтобы нельзя было угадать что именно неверно
            return {'error': 'Invalid username or password'}, 401

        access_token = create_access_token(identity=str(user.id))
        refresh_token = secrets.token_hex(32)

        # сохраняем новый refresh токен в базу
        new_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.token_repo.add(new_refresh_token)
        db.session.commit()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }, 200

    def refresh(self, refresh_token):
        # обновление токена: проверяем refresh токен и выдаем новую пару
        # это называется "ротация токенов" - старый уничтожается, выдается новый
        if not refresh_token:
            return {'error': 'Refresh token missing'}, 400

        # ищем токен в базе и проверяем что он не аннулирован
        token_entry = self.token_repo.get_valid_token(refresh_token)
        if not token_entry:
            return {'error': 'Invalid refresh token'}, 401

        # проверяем что срок жизни токена не истек
        if token_entry.expires_at < datetime.utcnow():
            return {'error': 'Refresh token expired'}, 401

        # аннулируем старый refresh токен (ротация - ключевая фишка безопасности)
        new_refresh_token_str = secrets.token_hex(32)
        token_entry.revoked = True

        # создаем новый refresh токен
        new_token_entry = RefreshToken(
            token=new_refresh_token_str,
            user_id=token_entry.user_id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.token_repo.add(new_token_entry)
        db.session.commit()

        # генерируем новый access token
        access_token = create_access_token(identity=str(token_entry.user_id))

        return {
            'access_token': access_token,
            'refresh_token': new_refresh_token_str
        }, 200

    def logout(self, refresh_token):
        # выход: помечаем refresh токен как revoked в базе данных
        # даже если у кого-то есть этот токен - он больше не сработает
        if refresh_token:
            token_entry = self.token_repo.get_token(refresh_token)
            if token_entry:
                token_entry.revoked = True
                db.session.commit()
        return {'message': 'Logged out successfully'}, 200

    def delete_user(self, user_id):
        # удаление аккаунта - каскадно удаляются все колоды и карточки пользователя
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        self.user_repo.delete(user)
        db.session.commit()
        return {'message': 'User deleted successfully'}, 200
