# сервис для работы с колодами и карточками
# тут самая сложная логика: загрузка pdf, работа с minio (хранилище файлов) и вызов ai

from models import db, Deck, Card, UserStats
import io
import time
from minio import Minio
from config import Config
from ai_service import generate_cards_from_text  # функция для генерации карточек через ai
import PyPDF2

# создаем клиент для minio - это наше хранилище файлов (как s3 бакет)
minio_client = Minio(
    Config.MINIO_ENDPOINT,
    access_key=Config.MINIO_ACCESS_KEY,
    secret_key=Config.MINIO_SECRET_KEY,
    secure=Config.MINIO_SECURE
)


def extract_text_from_pdf(file_source):
    # читаем pdf и вытаскиваем из него весь текст постранично
    text = ""
    try:
        # file_source может быть путем к файлу или потоком байт (BytesIO)
        if isinstance(file_source, str):
            file_obj = open(file_source, 'rb')
        else:
            file_obj = file_source

        pdf_reader = PyPDF2.PdfReader(file_obj)
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Страница {page_num + 1} ---\n{page_text}"

        if isinstance(file_source, str):
            file_obj.close()

        return text
    except Exception as e:
        raise Exception(f"Ошибка при чтении PDF: {str(e)}")


class DeckService:
    # получает репозитории через конструктор - dependency injection
    def __init__(self, deck_repo, card_repo, user_repo, stats_repo):
        self.deck_repo = deck_repo    # для работы с колодами
        self.card_repo = card_repo    # для работы с карточками
        self.user_repo = user_repo    # для поиска пользователя
        self.stats_repo = stats_repo  # для обновления счетчика колод в статистике

    def upload_and_generate(self, user_id, file, filename, mode):
        # основной метод: принимает pdf, загружает в minio, извлекает текст, генерирует карточки через ai
        timestamp = int(time.time())
        saved_filename = f"upload_{timestamp}.pdf"  # уникальное имя файла

        # читаем файл в память
        file_content = file.read()
        file_size = len(file_content)
        file_stream = io.BytesIO(file_content)  # создаем поток из байт для повторного чтения

        # загружаем pdf в minio (хранилище файлов) - если не получилось, продолжаем без этого
        bucket_name = Config.MINIO_BUCKET
        try:
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)  # создаем бакет если его нет
            minio_client.put_object(
                bucket_name,
                saved_filename,
                io.BytesIO(file_content),
                length=file_size,
                content_type='application/pdf'
            )
        except Exception as e:
            print(f"Ошибка загрузки в MinIO: {e}")  # логируем ошибку но не падаем

        # извлекаем текст из pdf
        file_stream.seek(0)  # перематываем поток в начало
        text = extract_text_from_pdf(file_stream)

        # проверяем что текст не пустой
        if not text or len(text.strip()) < 50:
            return {'error': 'Не удалось извлечь текст из PDF или текст слишком короткий'}, 400

        # отправляем текст в ai и получаем список карточек (вопрос-ответ)
        result = generate_cards_from_text(text, mode)
        if 'error' in result:
            return result, 500

        # создаем колоду в базе данных
        deck_title = filename.rsplit('.', 1)[0]  # название файла без расширения
        deck = Deck(
            title=deck_title,
            description=f"Карточки из файла {filename}",
            user_id=user_id
        )
        self.deck_repo.add(deck)
        db.session.flush()  # flush чтобы получить id новой колоды

        # создаем карточки и добавляем в базу
        created_cards = []
        for card_data in result['cards']:
            card = Card(
                question=card_data['question'],
                answer=card_data['answer'],
                source=card_data.get('source', 'Неизвестно'),
                deck_id=deck.id
            )
            self.card_repo.add(card)
            created_cards.append(card)

        # обновляем счетчик колод в статистике пользователя
        user_stats = self.stats_repo.get_by_user_id(user_id)
        if user_stats:
            user_stats.total_decks_created += 1

        db.session.commit()  # сохраняем всё в базу за одну транзакцию

        # добавляем реальные id карточек из бд в результат
        for i, card in enumerate(created_cards):
            result['cards'][i]['id'] = card.id

        result['mode'] = mode
        result['deck_id'] = deck.id
        return result, 200

    def get_user_decks(self, user_id, sort_by, page, per_page):
        # возвращаем постраничный список колод пользователя
        return self.deck_repo.get_user_decks(user_id, sort_by, page, per_page)

    def get_deck(self, deck_id):
        # возвращаем одну колоду по id
        return self.deck_repo.get_by_id(deck_id)

    def update_deck(self, deck_id, current_user_id, data):
        # обновляем название/описание/эмодзи колоды - только если ты её владелец
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {'error': 'Not found'}, 404
        # проверяем что пользователь является владельцем этой колоды
        if deck.user_id != current_user_id:
            return {'error': 'Unauthorized'}, 403

        if 'title' in data:
            deck.title = data['title']
        if 'description' in data:
            deck.description = data['description']
        if 'emoji' in data:
            deck.emoji = data['emoji']

        db.session.commit()
        return deck.to_dict(), 200

    def delete_deck(self, deck_id):
        # удаляем колоду - все карточки удаляются каскадом через relationship
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {'error': 'Not found'}, 404
        self.deck_repo.delete(deck)
        db.session.commit()
        return {'message': 'Колода удалена'}, 200

    def update_card(self, card_id, data):
        # обновляем содержимое карточки (вопрос/ответ/источник)
        card = self.card_repo.get_by_id(card_id)
        if not card:
            return {'error': 'Not found'}, 404

        if 'question' in data:
            card.question = data['question']
        if 'answer' in data:
            card.answer = data['answer']
        if 'source' in data:
            card.source = data['source']

        db.session.commit()
        return card.to_dict(), 200

    def delete_card(self, card_id):
        # удаляем конкретную карточку из колоды
        card = self.card_repo.get_by_id(card_id)
        if not card:
            return {'error': 'Not found'}, 404
        self.card_repo.delete(card)
        db.session.commit()
        return {'message': 'Карточка удалена'}, 200

    def create_card(self, deck_id, data):
        # создаем новую карточку вручную (не через ai, а руками)
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {'error': 'Not found'}, 404

        card = Card(
            question=data['question'],
            answer=data['answer'],
            source=data.get('source', 'Создано вручную'),
            deck_id=deck_id
        )
        self.card_repo.add(card)
        db.session.commit()
        return card.to_dict(), 201
