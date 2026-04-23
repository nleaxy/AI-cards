# Интеграционные тесты для подсистемы аутентификации и сессий
import pytest

def test_register_success(client):
    # Регистрация с корректными (новыми) данными
    response = client.post('/api/auth/register', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'strongpassword'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'message' in data
    assert data['message'] == 'User registered successfully'

def test_register_duplicate_email(client, test_user):
    # Формирование ошибки при регистрации на уже занятую почту
    response = client.post('/api/auth/register', json={
        'username': 'anotheruser',
        'email': test_user['email'],
        'password': 'strongpassword'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'email already exists' in data['error'].lower()

def test_login_success(client, test_user):
    # Вход с верными данными и проверка на выдачу куки с Refresh Token
    response = client.post('/api/auth/login', json={
        'username': test_user['username'],
        'password': test_user['password']
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'user' in data
    
    cookies = response.headers.getlist('Set-Cookie')
    assert any('refresh_token=' in cookie for cookie in cookies)

def test_login_invalid_credentials(client, test_user):
    # Вход с неверным паролем, проверка отказа в доступе
    response = client.post('/api/auth/login', json={
        'username': test_user['username'],
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data

def test_logout(client, test_user, auth_headers):
    # Логаут: проверка очистки сессионной куки (удаление токена)
    login_response = client.post('/api/auth/login', json={
        'username': test_user['username'],
        'password': test_user['password']
    })
    
    refresh_token = None
    for cookie in login_response.headers.getlist('Set-Cookie'):
        if 'refresh_token=' in cookie:
            refresh_token = cookie.split(';')[0].split('=')[1]
            break
            
    client.set_cookie('refresh_token', refresh_token, domain='localhost')
            
    response = client.post('/api/auth/logout', headers=auth_headers)
    assert response.status_code == 200
    
    cookies = response.headers.getlist('Set-Cookie')
    assert any('refresh_token=;' in cookie or 'Expires=Thu, 01 Jan 1970' in cookie for cookie in cookies)

def test_protected_route_missing_token(client):
    # Доступ к защищенным данным без токена
    response = client.get('/api/decks')
    assert response.status_code == 401

def test_protected_route_with_token(client, auth_headers):
    # Корректный доступ к защищенным ресурсам по валидному Access Token
    response = client.get('/api/decks', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.get_json()['decks'], list)
