from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с колодами
    decks = db.relationship('Deck', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }


class Deck(db.Model):
    __tablename__ = 'decks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_studied = db.Column(db.DateTime)
    
    # Связь с карточками
    cards = db.relationship('Card', backref='deck', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_cards=False):
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_studied': self.last_studied.isoformat() if self.last_studied else None,
            'card_count': len(self.cards)
        }
        if include_cards:
            result['cards'] = [card.to_dict() for card in self.cards]
        return result


class Card(db.Model):
    __tablename__ = 'cards'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(200))
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Статистика по карточке
    times_studied = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    last_studied = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'source': self.source,
            'deck_id': self.deck_id,
            'times_studied': self.times_studied,
            'times_correct': self.times_correct,
            'accuracy': (self.times_correct / self.times_studied * 100) if self.times_studied > 0 else 0
        }


class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    cards_studied = db.Column(db.Integer, default=0)
    cards_correct = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'deck_id': self.deck_id,
            'date': self.date.isoformat(),
            'cards_studied': self.cards_studied,
            'cards_correct': self.cards_correct,
            'accuracy': (self.cards_correct / self.cards_studied * 100) if self.cards_studied > 0 else 0
        }


class UserStats(db.Model):
    __tablename__ = 'user_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    total_decks_created = db.Column(db.Integer, default=0)  # Включая удаленные
    unique_cards_studied = db.Column(db.Text, default='[]')  # JSON список ID изученных карточек
    max_correct_streak = db.Column(db.Integer, default=0)   # Максимальная серия
    current_streak = db.Column(db.Integer, default=0)       # Текущая серия
    current_streak_cards = db.Column(db.Text, default='[]') # JSON список карточек в текущей серии
    
    user = db.relationship('User', backref='stats_record', uselist=False)
    
    def get_unique_cards_studied(self):
        """Получить список уникальных изученных карточек"""
        try:
            return json.loads(self.unique_cards_studied)
        except:
            return []
    
    def set_unique_cards_studied(self, card_ids):
        """Установить список уникальных изученных карточек"""
        self.unique_cards_studied = json.dumps(list(set(card_ids)))
    
    def add_unique_card(self, card_id):
        """Добавить карточку в изученные"""
        cards = self.get_unique_cards_studied()
        if card_id not in cards:
            cards.append(card_id)
            self.set_unique_cards_studied(cards)
            return True
        return False
    
    def get_current_streak_cards(self):
        """Получить список карточек в текущей серии"""
        try:
            return json.loads(self.current_streak_cards)
        except:
            return []
    
    def set_current_streak_cards(self, card_ids):
        """Установить список карточек в текущей серии"""
        self.current_streak_cards = json.dumps(card_ids)
    
    def reset_streak(self):
        """Сбросить текущую серию"""
        self.current_streak = 0
        self.set_current_streak_cards([])
    
    def increment_streak(self, card_id):
        """Увеличить серию если карточка уникальная для текущей серии"""
        streak_cards = self.get_current_streak_cards()
        if card_id not in streak_cards:
            streak_cards.append(card_id)
            self.set_current_streak_cards(streak_cards)
            self.current_streak = len(streak_cards)
            
            # Обновляем максимальную серию если превышена
            if self.current_streak > self.max_correct_streak:
                self.max_correct_streak = self.current_streak
            
            return True
        return False
    
    def reset_stats(self):
        """Полный сброс статистики"""
        self.total_decks_created = 0
        self.set_unique_cards_studied([])
        self.max_correct_streak = 0
        self.reset_streak()
    
    def to_dict(self):
        return {
            'total_decks': self.total_decks_created,
            'cards_studied': len(self.get_unique_cards_studied()),
            'max_streak': self.max_correct_streak,
            'current_streak': self.current_streak
        }