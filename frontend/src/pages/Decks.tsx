import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { BookOpen, Edit, Trash2, Play, ArrowUpDown, LogIn, Download, ChevronLeft, ChevronRight, Filter, Search } from 'lucide-react';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../api/client';
import SEO from '../components/SEO';

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

  const [searchParams, setSearchParams] = useSearchParams();
  const sortBy = searchParams.get('sort_by') || 'newest';
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  const searchQuery = searchParams.get('search') || '';
  const minCards = searchParams.get('min_cards') || '';
  const maxCards = searchParams.get('max_cards') || '';
  const dateFrom = searchParams.get('date_from') || '';
  const dateTo = searchParams.get('date_to') || '';

  const [totalPages, setTotalPages] = useState(1);
  const [needsAuth, setNeedsAuth] = useState<boolean>(false);
  const { token, user } = useAuth();

  // Local state for the filter form
  const [localSearch, setLocalSearch] = useState(searchQuery);
  const [localMin, setLocalMin] = useState(minCards);
  const [localMax, setLocalMax] = useState(maxCards);
  const [localDateFrom, setLocalDateFrom] = useState(dateFrom);
  const [localDateTo, setLocalDateTo] = useState(dateTo);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (user && token) {
      loadDecks();
      setNeedsAuth(false);
    } else {
      setLoading(false);
      setNeedsAuth(true);
      setDecks([]);
    }
  }, [sortBy, currentPage, searchQuery, minCards, maxCards, dateFrom, dateTo, token, user]);

  const loadDecks = async () => {
    setLoading(true);
    try {
      let qs = `/decks?sort_by=${sortBy}&page=${currentPage}&per_page=10`;
      if (searchQuery) qs += `&search=${encodeURIComponent(searchQuery)}`;
      if (minCards) qs += `&min_cards=${minCards}`;
      if (maxCards) qs += `&max_cards=${maxCards}`;
      if (dateFrom) qs += `&date_from=${dateFrom}`;
      if (dateTo) qs += `&date_to=${dateTo}`;

      const response = await apiFetch(qs, {
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

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    const newParams = new URLSearchParams(searchParams);

    if (localSearch) newParams.set('search', localSearch); else newParams.delete('search');
    if (localMin) newParams.set('min_cards', localMin); else newParams.delete('min_cards');
    if (localMax) newParams.set('max_cards', localMax); else newParams.delete('max_cards');
    if (localDateFrom) newParams.set('date_from', localDateFrom); else newParams.delete('date_from');
    if (localDateTo) newParams.set('date_to', localDateTo); else newParams.delete('date_to');

    newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const handleClearFilters = () => {
    setLocalSearch('');
    setLocalMin('');
    setLocalMax('');
    setLocalDateFrom('');
    setLocalDateTo('');
    const newParams = new URLSearchParams();
    newParams.set('sort_by', sortBy);
    setSearchParams(newParams);
  };

  const updateSort = (newSort: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('sort_by', newSort);
    newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const updatePage = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', newPage.toString());
    setSearchParams(newParams);
  };

  const handleExportDeck = async (deck: Deck) => {
    try {
      const response = await apiFetch(`/decks/${deck.id}/export`);

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
      const response = await apiFetch(`/decks/${deleteModal.deckId}`, {
        method: 'DELETE'
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
      const response = await apiFetch(`/decks/${emojiPicker.deckId}`, {
        method: 'PUT',
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

  if (loading && decks.length === 0) {
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
      <SEO
        title="Мои колоды"
        description="Управляйте своими учебными колодами: создавайте, изучайте, отслеживайте прогресс."
        canonical="/decks"
        noIndex={true}
      />
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Мои колоды</h1>
          <p>Управляйте своими наборами карточек</p>
        </div>
        <button className="btn btn-secondary" onClick={() => setShowFilters(!showFilters)}>
          <Filter size={18} />
          <span>{showFilters ? 'Скрыть фильтры' : 'Показать фильтры'}</span>
        </button>
      </div>

      {showFilters && (
        <form className="filters-panel" onSubmit={handleApplyFilters} style={{ background: 'var(--card-bg)', padding: '20px', borderRadius: '12px', marginBottom: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div className="form-group">
              <label>Поиск по названию/описанию</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <Search size={18} style={{ alignSelf: 'center', color: 'var(--text-light)' }} />
                <input type="text" value={localSearch} onChange={e => setLocalSearch(e.target.value)} placeholder="Поиск..." className="form-input" style={{ flex: 1 }} />
              </div>
            </div>

            <div className="form-group">
              <label>Кол-во карточек (от и до)</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input type="number" min="0" value={localMin} onChange={e => setLocalMin(e.target.value)} placeholder="Мин." className="form-input" />
                <input type="number" min="0" value={localMax} onChange={e => setLocalMax(e.target.value)} placeholder="Макс." className="form-input" />
              </div>
            </div>

            <div className="form-group">
              <label>Дата создания</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input type="date" value={localDateFrom} onChange={e => setLocalDateFrom(e.target.value)} className="form-input" />
                <input type="date" value={localDateTo} onChange={e => setLocalDateTo(e.target.value)} className="form-input" />
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button type="submit" className="btn btn-primary">Применить фильтры</button>
            <button type="button" className="btn btn-secondary" onClick={handleClearFilters}>Сбросить</button>
          </div>
        </form>
      )}

      {decks.length === 0 && !searchQuery && !minCards && !maxCards && !dateFrom && !dateTo ? (
        <div className="empty-state">
          <BookOpen size={64} className="empty-icon" />
          <h2>У вас пока нет колод</h2>
          <p>Загрузите PDF файл, чтобы создать первую колоду</p>
          <Link to="/upload" className="btn btn-primary btn-large">
            <span>Загрузить PDF</span>
          </Link>
        </div>
      ) : decks.length === 0 ? (
        <div className="empty-state">
          <Filter size={64} className="empty-icon" />
          <h2>Ничего не найдено</h2>
          <p>Попробуйте изменить параметры фильтрации</p>
          <button className="btn btn-secondary" onClick={handleClearFilters}>
            Сбросить фильтры
          </button>
        </div>
      ) : (
        <>
          <div className="decks-controls">
            <div className="sort-buttons">
              <ArrowUpDown size={20} />
              <span>Сортировка:</span>
              <button
                className={`sort-btn ${sortBy === 'newest' ? 'active' : ''}`}
                onClick={() => updateSort('newest')}
              >
                Новые
              </button>
              <button
                className={`sort-btn ${sortBy === 'oldest' ? 'active' : ''}`}
                onClick={() => updateSort('oldest')}
              >
                Старые
              </button>
              <button
                className={`sort-btn ${sortBy === 'name' ? 'active' : ''}`}
                onClick={() => updateSort('name')}
              >
                По названию
              </button>
              <button
                className={`sort-btn ${sortBy === 'cards' ? 'active' : ''}`}
                onClick={() => updateSort('cards')}
              >
                По количеству карточек
              </button>
            </div>
            <div className="deck-count">
              Всего: <strong>{decks.length}</strong> {loading && <span style={{ fontSize: '0.8em', color: 'var(--text-light)' }}>(обновление...)</span>}
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
                onClick={() => updatePage(Math.max(1, currentPage - 1))}
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
                onClick={() => updatePage(Math.min(totalPages, currentPage + 1))}
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