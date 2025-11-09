from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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