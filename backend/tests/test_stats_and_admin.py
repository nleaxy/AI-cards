# Интеграционные тесты для ролевой модели (админка) и статистики
import pytest

def test_get_stats(client, auth_headers):
    # Отдача сводной персональной статистики для юзера
    response = client.get('/api/stats', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_decks' in data
    assert 'cards_studied' in data
    assert 'max_streak' in data
    assert 'current_streak' in data

def test_admin_access_denied_for_normal_user(client, auth_headers):
    # Обычным пользователям блокируются админ-маршруты (ошибка 403)
    response = client.get('/api/admin/users', headers=auth_headers)
    assert response.status_code == 403

def test_admin_access_allowed_for_admin(client, admin_headers):
    # Вход с админ-токеном дает право просматривать список пользователей
    response = client.get('/api/admin/users', headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_admin_change_role(client, admin_headers, test_user):
    # Успешное присвоение роли 'admin' через админ-панель
    user_id = test_user['id']
    response = client.put(f'/api/admin/users/{user_id}/role', headers=admin_headers, json={'role': 'admin'})
    data = response.get_json()
    assert 'message' in data
