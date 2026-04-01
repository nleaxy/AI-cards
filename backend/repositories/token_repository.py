# репозиторий для работы с refresh токенами в базе данных
# токены хранятся в таблице refresh_tokens и могут быть аннулированы

from models import db, RefreshToken


class TokenRepository:
    def get_valid_token(self, token_str):
        # ищем активный (не аннулированный) refresh токен по его строке
        return RefreshToken.query.filter_by(token=token_str, revoked=False).first()

    def get_token(self, token_str):
        # ищем любой refresh токен по строке (даже уже аннулированный)
        return RefreshToken.query.filter_by(token=token_str).first()

    def add(self, token):
        # добавляем новый refresh токен в базу данных
        db.session.add(token)
