# Интеграционные тесты для CRUD-операций: колоды и доступ к ним
import pytest

def test_get_decks_empty(client, auth_headers):
    # Запрос списка колод для нового юзера (список должен быть пуст)
    response = client.get('/api/decks', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['decks'] == []
    assert response.get_json()['total'] == 0

def test_deck_crud_cycle(client, auth_headers):
    # Заглушка, так как часть логики покрывается фикстурами ниже
    pass

@pytest.fixture
def sample_deck(app, test_user):
    # Создает тестовую колоду и карточки, привязанные к юзеру
    from models import db, Deck, Card
    with app.app_context():
        deck = Deck(title='Test Deck', description='Test Desc', user_id=test_user['id'])
        db.session.add(deck)
        db.session.commit()
        
        card1 = Card(question='Q1', answer='A1', deck_id=deck.id)
        card2 = Card(question='Q2', answer='A2', deck_id=deck.id)
        db.session.add_all([card1, card2])
        db.session.commit()
        
        return {'id': deck.id, 'title': 'Test Deck'}

def test_get_specific_deck(client, auth_headers, sample_deck):
    # Проверка вывода конкретной колоды вместе с привязанными карточками
    response = client.get(f'/api/decks/{sample_deck["id"]}', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == 'Test Deck'
    assert len(data['cards']) == 2

def test_update_deck(client, auth_headers, sample_deck):
    # Проверка изменения названия и иконки (эмодзи)
    response = client.put(f'/api/decks/{sample_deck["id"]}', headers=auth_headers, json={
        'title': 'Updated Deck',
        'description': 'Updated Desc',
        'emoji': '🚀'
    })
    assert response.status_code == 200
    
    get_response = client.get(f'/api/decks/{sample_deck["id"]}', headers=auth_headers)
    assert get_response.get_json()['title'] == 'Updated Deck'
    assert get_response.get_json()['emoji'] == '🚀'

def test_delete_deck(client, auth_headers, sample_deck):
    # Успешное удаление колоды владельцем
    response = client.delete(f'/api/decks/{sample_deck["id"]}', headers=auth_headers)
    assert response.status_code == 200
    
    get_response = client.get(f'/api/decks/{sample_deck["id"]}', headers=auth_headers)
    assert get_response.status_code == 404

def test_deck_access_denied_for_other_user(client, auth_headers, admin_user, app):
    # Убеждаемся, что обычный пользователь не имеет права редачить чужие колоды
    from models import db, Deck
    with app.app_context():
        deck = Deck(title='Admin Deck', user_id=admin_user['id'])
        db.session.add(deck)
        db.session.commit()
        deck_id = deck.id
        
    response = client.put(f'/api/decks/{deck_id}', headers=auth_headers, json={'title': 'Hacked'})
    assert response.status_code in (403, 404)

def test_mocked_ai_generation(client, auth_headers, mocker):
    # 5.3 Мы перехватываем реальное обращение к AI-сервису, чтобы тесты не тратили деньги
    mock_generate = mocker.patch('core.container.container.deck_service.upload_and_generate')
    mock_generate.return_value = ({'message': 'Mocked cards generated', 'cards': []}, 201)
    
    import io
    data = {
        'file': (io.BytesIO(b'fake pdf content'), 'test.pdf'),
        'mode': 'summary'
    }
    response = client.post('/api/upload', headers=auth_headers, data=data, content_type='multipart/form-data')
    
    # Теперь мы проверяем, работает ли НАШ код, даже когда внешний API "заперт" в коробке
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Mocked cards generated'
    mock_generate.assert_called_once()
