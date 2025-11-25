import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Edit, Trash2, Play, ArrowUpDown, LogIn } from 'lucide-react';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';

interface Deck {
  id: string;
  title: string;
  description: string;
  card_count: number;
  created_at: string;
  last_studied?: string;
}

interface DeleteModalState {
  isOpen: boolean;
  deckId: string | null;
  deckTitle: string;
}

const Decks: React.FC = () => {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [deleteModal, setDeleteModal] = useState<DeleteModalState>({ isOpen: false, deckId: null, deckTitle: '' });
  const [sortBy, setSortBy] = useState<string>('newest');
  const [needsAuth, setNeedsAuth] = useState<boolean>(false);
  const { token, user } = useAuth();

  useEffect(() => {
    if (user && token) {
      loadDecks();
      setNeedsAuth(false);
    } else {
      setLoading(false);
      setNeedsAuth(true);
      setDecks([]);
    }
  }, [sortBy, token, user]);

  const loadDecks = async () => {
    if (decks.length === 0) {
      setLoading(true);
    }
    try {
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`http://localhost:5000/api/decks?sort_by=${sortBy}`, {
        headers,
        cache: 'no-cache'
      });

      if (response.status === 401) {
        setNeedsAuth(true);
        setDecks([]);
        setLoading(false);
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to load decks');
      }

      const data = await response.json();
      setDecks(data.decks || []);
      setNeedsAuth(false);
    } catch (error) {
      console.error('Error loading decks:', error);
      setDecks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDeck = async () => {
    if (!deleteModal.deckId) return;

    try {
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`http://localhost:5000/api/decks/${deleteModal.deckId}`, {
        method: 'DELETE',
        headers
      });

      if (response.ok) {
        loadDecks();
        setDeleteModal({ isOpen: false, deckId: null, deckTitle: '' });
      } else {
        alert('Ошибка при удалении колоды');
      }
    } catch (error) {
      console.error('Error deleting deck:', error);
      alert('Ошибка соединения');
    }
  };

  const openDeleteModal = (deck: Deck) => {
    setDeleteModal({
      isOpen: true,
      deckId: deck.id,
      deckTitle: deck.title
    });
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Загрузка колод...</div>
      </div>
    );
  }

  if (needsAuth) {
    return (
      <div className="container page-decks">
        <div className="page-header">
          <h1>Мои колоды</h1>
          <p>Управляйте своими наборами карточек</p>
        </div>
        <div className="empty-state">
          <LogIn size={64} className="empty-icon" />
          <h2>Требуется авторизация</h2>
          <p>Войдите в аккаунт, чтобы просматривать свои колоды</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container page-decks">
      <div className="page-header">
        <h1>Мои колоды</h1>
        <p>Управляйте своими наборами карточек</p>
      </div>

      {decks.length === 0 ? (
        <div className="empty-state">
          <BookOpen size={64} className="empty-icon" />
          <h2>У вас пока нет колод</h2>
          <p>Загрузите PDF файл, чтобы создать первую колоду</p>
          <Link to="/upload" className="btn btn-primary btn-large">
            <span>Загрузить PDF</span>
          </Link>
        </div>
      ) : (
        <>
          <div className="decks-controls">
            <div className="sort-buttons">
              <ArrowUpDown size={20} />
              <span>Сортировка:</span>
              <button
                className={`sort-btn ${sortBy === 'newest' ? 'active' : ''}`}
                onClick={() => setSortBy('newest')}
              >
                Новые
              </button>
              <button
                className={`sort-btn ${sortBy === 'oldest' ? 'active' : ''}`}
                onClick={() => setSortBy('oldest')}
              >
                Старые
              </button>
              <button
                className={`sort-btn ${sortBy === 'name' ? 'active' : ''}`}
                onClick={() => setSortBy('name')}
              >
                По названию
              </button>
              <button
                className={`sort-btn ${sortBy === 'cards' ? 'active' : ''}`}
                onClick={() => setSortBy('cards')}
              >
                По количеству
              </button>
            </div>
            <div className="deck-count">
              Всего: <strong>{decks.length}</strong>
            </div>
          </div>

          <div className="decks-grid">
            {decks.map((deck) => (
              <div key={deck.id} className="deck-card">
                <div className="deck-header">
                  <BookOpen size={32} className="deck-icon" />
                  <h3>{deck.title}</h3>
                </div>

                <p className="deck-description">{deck.description}</p>

                <div className="deck-stats">
                  <span className="deck-stat">
                    <strong>{deck.card_count}</strong> карточек
                  </span>
                  {deck.last_studied && (
                    <span className="deck-stat-small">
                      Последнее изучение: {new Date(deck.last_studied).toLocaleDateString('ru-RU')}
                    </span>
                  )}
                </div>

                <div className="deck-actions">
                  <Link
                    to={`/learn/${deck.id}`}
                    className="btn btn-primary"
                  >
                    <Play size={18} />
                    <span>Изучать</span>
                  </Link>
                  <Link
                    to={`/manage/${deck.id}`}
                    className="btn btn-secondary"
                  >
                    <Edit size={18} />
                    <span>Управление</span>
                  </Link>
                  <button
                    className="btn btn-wrong"
                    onClick={() => openDeleteModal(deck)}
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <Modal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, deckId: null, deckTitle: '' })}
        onConfirm={handleDeleteDeck}
        title="Удалить колоду?"
        message={`Вы уверены, что хотите удалить колоду "${deleteModal.deckTitle}"? Все карточки в ней будут удалены. Это действие нельзя отменить.`}
        confirmText="Удалить колоду"
        danger={true}
      />
    </div>
  );
};

export default Decks;