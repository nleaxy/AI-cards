# api routes для авторизации - регистрация, вход, обновление токена, выход, удаление аккаунта
# refresh token теперь хранится в httponly cookie - javascript не имеет к нему доступа

from flask import Blueprint, request, jsonify, make_response
from core.container import container
from flask_jwt_extended import jwt_required, get_jwt_identity

# создаем blueprint - это как мини-приложение с группой маршрутов
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def set_refresh_cookie(response, refresh_token):
    # прописываем refresh token в httponly cookie - браузер сам хранит и отправляет его
    # httponly=True означает что javascript не может прочитать этот cookie (защита от xss)
    # samesite='Lax' означает что cookie отправляется только с того же сайта (защита от csrf)
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,        # недоступен для javascript
        samesite='Lax',       # защита от csrf атак
        secure=False,         # True в продакшне (только https), False для localhost
        max_age=7 * 24 * 3600  # живет 7 дней
    )
    return response


@auth_bp.route('/register', methods=['POST'])
def register():
    # регистрация нового пользователя - берем данные из запроса и отдаем в сервис
    data = request.json
    result, status_code = container.auth_service.register(
        data.get('username'),
        data.get('email'),
        data.get('password')
    )
    if status_code == 201:
        # вытаскиваем refresh token из ответа и кладем в httponly cookie
        refresh_token = result.pop('refresh_token', None)
        response = make_response(jsonify(result), status_code)
        if refresh_token:
            set_refresh_cookie(response, refresh_token)
        return response
    return jsonify(result), status_code


@auth_bp.route('/login', methods=['POST'])
def login():
    # вход в аккаунт - проверяем логин/пароль через сервис
    data = request.json
    result, status_code = container.auth_service.login(
        data.get('username'),
        data.get('password')
    )
    if status_code == 200:
        # вытаскиваем refresh token из ответа и кладем в httponly cookie
        refresh_token = result.pop('refresh_token', None)
        response = make_response(jsonify(result), status_code)
        if refresh_token:
            set_refresh_cookie(response, refresh_token)
        return response
    return jsonify(result), status_code


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    # обновление access токена - refresh token читаем из cookie, а не из тела запроса
    # браузер автоматически отправляет cookie с каждым запросом
    refresh_token = request.cookies.get('refresh_token')
    result, status_code = container.auth_service.refresh(refresh_token)
    if status_code == 200:
        # кладем новый refresh token обратно в cookie (ротация токенов)
        new_refresh_token = result.pop('refresh_token', None)
        response = make_response(jsonify(result), status_code)
        if new_refresh_token:
            set_refresh_cookie(response, new_refresh_token)
        return response
    return jsonify(result), status_code


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()  # этот маршрут требует валидный access token
def logout():
    # выход из аккаунта - аннулируем refresh токен в базе данных и удаляем cookie
    refresh_token = request.cookies.get('refresh_token')
    result, status_code = container.auth_service.logout(refresh_token)
    response = make_response(jsonify(result), status_code)
    # удаляем httponly cookie из браузера
    response.delete_cookie('refresh_token', samesite='Lax')
    return response


@auth_bp.route('/user', methods=['DELETE'])
@jwt_required()  # только авторизованный пользователь может удалить себя
def delete_user():
    # удаление своего аккаунта - берем id из токена и удаляем через сервис
    user_id = int(get_jwt_identity())
    result, status_code = container.auth_service.delete_user(user_id)
    response = make_response(jsonify(result), status_code)
    if status_code == 200:
        response.delete_cookie('refresh_token', samesite='Lax')
    return response
