# Service for handling decks, cards, and file storage (MinIO)

from models import db, Deck, Card, UserStats, DeckFile
import io
import time
import urllib3
from minio import Minio
from config import Config
from ai_service import generate_cards_from_text
import PyPDF2

# Short timeout for MinIO so the backend doesn't hang if the storage is down
http_client = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=2.0, read=2.0),
    retries=urllib3.Retry(total=0)
)

# MinIO client - S3-compatible object storage
minio_client = Minio(
    Config.MINIO_ENDPOINT,
    access_key=Config.MINIO_ACCESS_KEY,
    secret_key=Config.MINIO_SECRET_KEY,
    secure=Config.MINIO_SECURE,
    http_client=http_client
)


def extract_text_from_pdf(file_source):
    # Read a PDF file and extract all text page by page
    text = ""
    try:
        # file_source can be a file path string or a BytesIO stream
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
    # Receives repositories via constructor injection (dependency injection)
    def __init__(self, deck_repo, card_repo, user_repo, stats_repo):
        self.deck_repo = deck_repo    # deck CRUD
        self.card_repo = card_repo    # card CRUD
        self.user_repo = user_repo    # user lookups
        self.stats_repo = stats_repo  # update deck count in user stats

    def upload_and_generate(self, user_id, file, filename, mode):
        # Main upload flow: read PDF, store in MinIO, extract text, generate cards via AI
        timestamp = int(time.time())
        saved_filename = f"upload_{timestamp}.pdf"

        # Read the file into memory so we can both upload it and parse it
        file_content = file.read()
        file_size = len(file_content)
        file_stream = io.BytesIO(file_content)

        # Upload PDF to MinIO - if this fails we log and continue without blocking
        bucket_name = Config.MINIO_BUCKET
        try:
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
            minio_client.put_object(
                bucket_name,
                saved_filename,
                io.BytesIO(file_content),
                length=file_size,
                content_type='application/pdf'
            )
        except Exception as e:
            print(f"MinIO upload error (non-fatal): {e}")

        # Extract text from the PDF
        file_stream.seek(0)
        text = extract_text_from_pdf(file_stream)

        if not text or len(text.strip()) < 50:
            return {'error': 'Не удалось извлечь текст из PDF или текст слишком короткий'}, 400

        # Send text to AI and get back a list of question-answer cards
        result = generate_cards_from_text(text, mode)
        if 'error' in result:
            return result, 500

        # Create a deck in the database
        deck_title = filename.rsplit('.', 1)[0]  # strip file extension
        deck = Deck(
            title=deck_title,
            description=f"Карточки из файла {filename}",
            user_id=user_id
        )
        self.deck_repo.add(deck)
        db.session.flush()  # flush to get the new deck's ID

        # Create card records
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

        # Increment the user's total decks counter
        user_stats = self.stats_repo.get_by_user_id(user_id)
        if user_stats:
            user_stats.total_decks_created += 1

        db.session.commit()

        # Patch the result cards with their real database IDs
        for i, card in enumerate(created_cards):
            result['cards'][i]['id'] = card.id

        result['mode'] = mode
        result['deck_id'] = deck.id
        return result, 200

    def get_user_decks(self, user_id, sort_by, page, per_page,
                       search=None, min_cards=None, max_cards=None,
                       date_from=None, date_to=None):
        # Return a paginated list of decks for a user with optional filtering
        return self.deck_repo.get_user_decks(
            user_id, sort_by, page, per_page,
            search=search, min_cards=min_cards, max_cards=max_cards,
            date_from=date_from, date_to=date_to
        )

    def get_deck(self, deck_id):
        return self.deck_repo.get_by_id(deck_id)

    def update_deck(self, deck_id, current_user_id, data):
        # Update deck title/description/emoji - only the owner can do this
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {'error': 'Not found'}, 404
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
        # Delete a deck; all child cards are removed via cascade
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {'error': 'Not found'}, 404
        self.deck_repo.delete(deck)
        db.session.commit()
        return {'message': 'Колода удалена'}, 200

    def update_card(self, card_id, data):
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
        card = self.card_repo.get_by_id(card_id)
        if not card:
            return {'error': 'Not found'}, 404
        self.card_repo.delete(card)
        db.session.commit()
        return {'message': 'Карточка удалена'}, 200

    def create_card(self, deck_id, data):
        # Manually create a new card (not AI-generated)
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

    def upload_deck_file(self, deck_id, current_user_id, file, filename):
        # Check deck ownership
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {'error': 'Колода не найдена'}, 404
        if deck.user_id != current_user_id:
            return {'error': 'Нет прав'}, 403

        # Validate file size (max 10 MB)
        file_content = file.read()
        file_size = len(file_content)
        if file_size > 10 * 1024 * 1024:
            return {'error': 'Файл слишком большой (макс 10 MB)'}, 400

        allowed_ext = {'pdf', 'png', 'jpg', 'jpeg', 'docx'}
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in allowed_ext:
            return {'error': 'Недопустимый тип файла'}, 400

        # Upload to MinIO
        timestamp = int(time.time())
        object_name = f"deck_{deck_id}_{timestamp}_{filename}"
        bucket_name = Config.MINIO_BUCKET

        try:
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
            minio_client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(file_content),
                length=file_size,
                content_type=file.content_type
            )
        except Exception as e:
            return {'error': f'Ошибка загрузки в хранилище: {str(e)}'}, 500

        # Save metadata to DB
        deck_file = DeckFile(
            deck_id=deck_id,
            object_name=object_name,
            original_name=filename,
            size_bytes=file_size,
            mime_type=file.content_type
        )
        db.session.add(deck_file)
        db.session.commit()

        return deck_file.to_dict(), 201

    def get_deck_files(self, deck_id, current_user_id):
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {'error': 'Колода не найдена'}, 404
        if deck.user_id != current_user_id:
            return {'error': 'Нет прав'}, 403

        files = DeckFile.query.filter_by(deck_id=deck_id).all()
        return [f.to_dict() for f in files], 200

    def get_file_url(self, file_id, current_user_id):
        deck_file = DeckFile.query.get(file_id)
        if not deck_file:
            return {'error': 'Файл не найден'}, 404

        deck = self.deck_repo.get_by_id(deck_file.deck_id)
        if deck.user_id != current_user_id:
            return {'error': 'Нет прав'}, 403

        try:
            # Presigned URL is valid for 1 hour
            url = minio_client.presigned_get_object(
                Config.MINIO_BUCKET,
                deck_file.object_name,
            )
            return {'url': url, 'original_name': deck_file.original_name}, 200
        except Exception as e:
            return {'error': f'Ошибка генерации ссылки: {str(e)}'}, 500

    def delete_deck_file(self, file_id, current_user_id):
        deck_file = DeckFile.query.get(file_id)
        if not deck_file:
            return {'error': 'Файл не найден'}, 404

        deck = self.deck_repo.get_by_id(deck_file.deck_id)
        if deck.user_id != current_user_id:
            return {'error': 'Нет прав'}, 403

        # Remove from MinIO
        try:
            minio_client.remove_object(Config.MINIO_BUCKET, deck_file.object_name)
        except Exception as e:
            print(f"MinIO delete error (non-fatal): {e}")

        # Remove from DB
        db.session.delete(deck_file)
        db.session.commit()
        return {'message': 'Файл удалён'}, 200
