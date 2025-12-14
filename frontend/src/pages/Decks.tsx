import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Edit, Trash2, Play, ArrowUpDown, LogIn, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';

interface Deck {
  id: string;
  title: string;
  description: string;
  card_count: number;
  created_at: string;

  last_studied?: string;
  emoji?: string;
}

const EMOJI_LIST = ['📚', '🎓', '🧠', '💡', '📝', '🇺🇸', '🇪🇸', '🇫🇷', '🇩🇪', '🇯🇵', '🇨🇳', '💻', '🐍', '⚛️', '🎨', '🎵', '⚽', '🎬', '✈️', '💼', '🚀', '⭐', '🔥', '✅'];

interface DeleteModalState {
  isOpen: boolean;
  deckId: string | null;
  deckTitle: string;
}

const Decks: React.FC = () => {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const [deleteModal, setDeleteModal] = useState<DeleteModalState>({ isOpen: false, deckId: null, deckTitle: '' });
  const [emojiPicker, setEmojiPicker] = useState<{ isOpen: boolean; deckId: string | null }>({ isOpen: false, deckId: null });
  const [sortBy, setSortBy] = useState<string>('newest');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
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
  }, [sortBy, token, user, currentPage]);

  const loadDecks = async () => {
    if (decks.length === 0) {
      setLoading(true);
    }
    try {
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`http://localhost:5000/api/decks?sort_by=${sortBy}&page=${currentPage}&per_page=10`, {
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
      setTotalPages(data.pages || 1);
      setNeedsAuth(false);
    } catch (error) {
      console.error('Error loading decks:', error);
      setDecks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleExportDeck = async (deck: Deck) => {
    try {
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`http://localhost:5000/api/decks/${deck.id}/export`, {
        headers
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${deck.title}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error exporting deck:', error);
      alert('Ошибка при экспорте колоды');
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

  const handleUpdateEmoji = async (emoji: string) => {
    if (!emojiPicker.deckId) return;

    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`http://localhost:5000/api/decks/${emojiPicker.deckId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ emoji })
      });

      if (response.ok) {
        setDecks(decks.map(d => d.id === emojiPicker.deckId ? { ...d, emoji } : d));
        setEmojiPicker({ isOpen: false, deckId: null });
      } else {
        alert('Ошибка при обновлении эмодзи');
      }
    } catch (error) {
      console.error('Error updating emoji:', error);
    }
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
                  <button
                    className="deck-icon-btn"
                    onClick={() => setEmojiPicker({ isOpen: true, deckId: deck.id })}
                    title="Изменить иконку"
                  >
                    {deck.emoji ? (
                      <span className="deck-emoji">{deck.emoji}</span>
                    ) : (
                      <BookOpen size={32} className="deck-icon" />
                    )}
                  </button>
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
                    className="btn btn-secondary"
                    onClick={() => handleExportDeck(deck)}
                    title="Скачать CSV для Anki"
                  >
                    <Download size={18} />
                  </button>
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

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-secondary"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft size={20} />
                Назад
              </button>
              <span className="pagination-info">
                Страница {currentPage} из {totalPages}
              </span>
              <button
                className="btn btn-secondary"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Вперед
                <ChevronRight size={20} />
              </button>
            </div>
          )}
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

      {emojiPicker.isOpen && (
        <div className="modal-overlay" onClick={() => setEmojiPicker({ isOpen: false, deckId: null })}>
          <div className="modal-content emoji-picker-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Выберите иконку</h2>
              <button className="modal-close" onClick={() => setEmojiPicker({ isOpen: false, deckId: null })}>×</button>
            </div>
            <div className="emoji-grid">
              {EMOJI_LIST.map(emoji => (
                <button
                  key={emoji}
                  className="emoji-btn"
                  onClick={() => handleUpdateEmoji(emoji)}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Decks;