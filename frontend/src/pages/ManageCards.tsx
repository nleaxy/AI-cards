import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Edit2, Trash2, Plus, Save, X } from 'lucide-react';
import Modal from '../components/Modal';
import DeckFilesPanel from '../components/DeckFilesPanel';
import { apiFetch } from '../api/client';
import SEO from '../components/SEO';

interface Card {
  id: string;
  question: string;
  answer: string;
  source: string;
  times_studied: number;
  times_correct: number;
  accuracy: number;
}

interface Deck {
  id: string;
  title: string;
  cards?: Card[];
}

interface CardForm {
  question: string;
  answer: string;
  source: string;
}

interface DeleteModalState {
  isOpen: boolean;
  cardId: string | null;
}

const ManageCards: React.FC = () => {
  const { deckId } = useParams<{ deckId: string }>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<CardForm>({ question: '', answer: '', source: '' });
  const [showAddForm, setShowAddForm] = useState<boolean>(false);
  const [newCard, setNewCard] = useState<CardForm>({ question: '', answer: '', source: '' });
  const [deleteModal, setDeleteModal] = useState<DeleteModalState>({ isOpen: false, cardId: null });

  useEffect(() => {
    loadDeck();
  }, [deckId]);

  const loadDeck = async () => {
    try {
      const response = await apiFetch(`/decks/${deckId}`);
      if (!response.ok) throw new Error('Failed to load deck');
      const data = await response.json();
      setDeck(data);
      setCards(data.cards || []);
    } catch (error) {
      console.error('Error loading deck:', error);
      alert('Ошибка загрузки колоды');
    }
  };

  const handleEdit = (card: Card) => {
    setEditingId(card.id);
    setEditForm({
      question: card.question,
      answer: card.answer,
      source: card.source
    });
  };

  const handleSave = async (cardId: string) => {
    try {
      const response = await apiFetch(`/cards/${cardId}`, {
        method: 'PUT',
        body: JSON.stringify(editForm)
      });

      if (response.ok) {
        setEditingId(null);
        loadDeck();
      } else {
        alert('Ошибка при сохранении');
      }
    } catch (error) {
      console.error('Error saving card:', error);
      alert('Ошибка соединения');
    }
  };

  const openDeleteModal = (cardId: string) => {
    setDeleteModal({ isOpen: true, cardId });
  };

  const handleDelete = async () => {
    if (!deleteModal.cardId) return;

    try {
      const response = await apiFetch(`/cards/${deleteModal.cardId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadDeck();
        setDeleteModal({ isOpen: false, cardId: null });
      } else {
        alert('Ошибка при удалении');
      }
    } catch (error) {
      console.error('Error deleting card:', error);
      alert('Ошибка соединения');
    }
  };

  const handleAddCard = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newCard.question || !newCard.answer) {
      alert('Заполните вопрос и ответ');
      return;
    }

    try {
      const response = await apiFetch(`/decks/${deckId}/cards`, {
        method: 'POST',
        body: JSON.stringify(newCard)
      });

      if (response.ok) {
        setNewCard({ question: '', answer: '', source: '' });
        setShowAddForm(false);
        loadDeck();
      } else {
        alert('Ошибка при добавлении');
      }
    } catch (error) {
      console.error('Error adding card:', error);
      alert('Ошибка соединения');
    }
  };

  if (!deck) {
    return <div className="container"><div className="loading">Загрузка...</div></div>;
  }

  return (
    <div className="container page-manage">
      <SEO
        title={`Управление: ${deck?.title || 'Колода'}`}
        noIndex={true}
      />
      <div className="page-header">
        <h1>Управление карточками</h1>
        <p>{deck.title}</p>
      </div>

      <DeckFilesPanel deckId={deckId!} />

      <div className="manage-actions" style={{ marginTop: '20px' }}>
        <button
          className="btn btn-primary"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          <Plus size={20} />
          <span>Добавить карточку</span>
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => navigate(`/learn/${deckId}`, { state: { cards } })}
        >
          <span>Начать изучение</span>
        </button>
      </div>

      {showAddForm && (
        <form className="card-form" onSubmit={handleAddCard}>
          <h3>Новая карточка</h3>
          <div className="form-group">
            <label>Вопрос:</label>
            <textarea
              value={newCard.question}
              onChange={(e) => setNewCard({ ...newCard, question: e.target.value })}
              rows={3}
              required
            />
          </div>
          <div className="form-group">
            <label>Ответ:</label>
            <textarea
              value={newCard.answer}
              onChange={(e) => setNewCard({ ...newCard, answer: e.target.value })}
              rows={3}
              required
            />
          </div>
          <div className="form-group">
            <label>Источник:</label>
            <input
              type="text"
              value={newCard.source}
              onChange={(e) => setNewCard({ ...newCard, source: e.target.value })}
              placeholder="Необязательно"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary">
              <Save size={18} />
              <span>Сохранить</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowAddForm(false)}
            >
              <X size={18} />
              <span>Отмена</span>
            </button>
          </div>
        </form>
      )}

      <div className="cards-list">
        {cards.map((card) => (
          <div key={card.id} className="card-item">
            {editingId === card.id ? (
              <div className="card-edit-form">
                <div className="form-group">
                  <label>Вопрос:</label>
                  <textarea
                    value={editForm.question}
                    onChange={(e) => setEditForm({ ...editForm, question: e.target.value })}
                    rows={3}
                  />
                </div>
                <div className="form-group">
                  <label>Ответ:</label>
                  <textarea
                    value={editForm.answer}
                    onChange={(e) => setEditForm({ ...editForm, answer: e.target.value })}
                    rows={3}
                  />
                </div>
                <div className="form-group">
                  <label>Источник:</label>
                  <input
                    type="text"
                    value={editForm.source}
                    onChange={(e) => setEditForm({ ...editForm, source: e.target.value })}
                  />
                </div>
                <div className="card-actions">
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => handleSave(card.id)}
                  >
                    <Save size={16} />
                    <span>Сохранить</span>
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setEditingId(null)}
                  >
                    <X size={16} />
                    <span>Отмена</span>
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="card-content">
                  <div className="card-section">
                    <strong>Вопрос:</strong>
                    <p>{card.question}</p>
                  </div>
                  <div className="card-section">
                    <strong>Ответ:</strong>
                    <p>{card.answer}</p>
                  </div>
                  <div className="card-meta">
                    <span className="card-source-tag">{card.source}</span>
                    {card.times_studied > 0 && (
                      <span className="card-stats">
                        📊 {card.accuracy.toFixed(0)}% ({card.times_correct}/{card.times_studied})
                      </span>
                    )}
                  </div>
                </div>
                <div className="card-actions">
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleEdit(card)}
                  >
                    <Edit2 size={16} />
                    <span>Редактировать</span>
                  </button>
                  <button
                    className="btn btn-wrong btn-sm"
                    onClick={() => openDeleteModal(card.id)}
                  >
                    <Trash2 size={16} />
                    <span>Удалить</span>
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      <Modal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, cardId: null })}
        onConfirm={handleDelete}
        title="Удалить карточку?"
        message="Вы уверены, что хотите удалить эту карточку? Это действие нельзя отменить."
        confirmText="Удалить"
        danger={true}
      />
    </div>
  );
};

export default ManageCards;