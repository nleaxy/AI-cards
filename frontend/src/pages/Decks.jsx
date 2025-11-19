import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Edit, Trash2, Play, ArrowUpDown } from 'lucide-react';
import Modal from '../components/Modal';

const Decks = () => {
  const [decks, setDecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, deckId: null, deckTitle: '' });
  const [sortBy, setSortBy] = useState('newest');

  useEffect(() => {
    loadDecks();
  }, []);

  const loadDecks = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/decks');
      const data = await response.json();
      setDecks(data.decks || []);
    } catch (error) {
      console.error('Error loading decks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDeck = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/decks/${deleteModal.deckId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadDecks();
      } else {
        alert('Ошибка при удалении колоды');
      }
    } catch (error) {
      console.error('Error deleting deck:', error);
      alert('Ошибка соединения');
    }
  };

  const openDeleteModal = (deck) => {
    setDeleteModal({
      isOpen: true,
      deckId: deck.id,
      deckTitle: deck.title
    });
  };

  const getSortedDecks = () => {
    const sorted = [...decks];
    
    switch (sortBy) {
      case 'newest':
        return sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      case 'oldest':
        return sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      case 'name':
        return sorted.sort((a, b) => a.title.localeCompare(b.title));
      case 'cards':
        return sorted.sort((a, b) => b.card_count - a.card_count);
      default:
        return sorted;
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Загрузка колод...</div>
      </div>
    );
  }

  const sortedDecks = getSortedDecks();

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
            {sortedDecks.map((deck) => (
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