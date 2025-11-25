import React, { useEffect, useState } from 'react';
import { BarChart3, BookOpen, CheckCircle, Flame, RotateCcw } from 'lucide-react';
import Modal from '../components/Modal';

interface Stats {
  total_decks: number;
  cards_studied: number;
  max_streak: number;
}

const Review: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [resetModal, setResetModal] = useState<boolean>(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = () => {
    fetch('http://localhost:5000/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error(err));
  };

  const handleResetStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/stats/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        loadStats();
      } else {
        alert('Ошибка при сбросе статистики');
      }
    } catch (error) {
      console.error('Error resetting stats:', error);
      alert('Ошибка соединения');
    }
  };

  if (!stats) {
    return (
      <div className="container page-review">
        <div className="loading">Загрузка статистики...</div>
      </div>
    );
  }

  return (
    <div className="container page-review">
      <div className="page-header">
        <h1>Ваша статистика</h1>
        <p>Отслеживайте свой прогресс в обучении</p>
      </div>

      <div className="stats-dashboard-simple">
        <div className="stat-card-large">
          <div className="stat-card-icon">
            <BookOpen size={48} />
          </div>
          <div className="stat-card-content">
            <div className="stat-card-value">{stats.total_decks}</div>
            <div className="stat-card-label">Колод создано</div>
            <div className="stat-card-description">
              Всего колод, включая удалённые
            </div>
          </div>
        </div>

        <div className="stat-card-large">
          <div className="stat-card-icon stat-icon-success">
            <CheckCircle size={48} />
          </div>
          <div className="stat-card-content">
            <div className="stat-card-value">{stats.cards_studied}</div>
            <div className="stat-card-label">Уникальных карточек</div>
            <div className="stat-card-description">
              Изучено уникальных карточек всего
            </div>
          </div>
        </div>

        <div className="stat-card-large">
          <div className="stat-card-icon stat-icon-fire">
            <Flame size={48} />
          </div>
          <div className="stat-card-content">
            <div className="stat-card-value">{stats.max_streak}</div>
            <div className="stat-card-label">Макс. серия верных</div>
            <div className="stat-card-description">
              Лучший результат уникальных правильных ответов подряд
            </div>
          </div>
        </div>
      </div>

      <div className="stats-info">
        <BarChart3 size={32} className="info-icon" />
        <h3>Ваша статистика сохраняется автоматически</h3>
        <p>Все данные привязаны к вашему аккаунту и будут доступны после авторизации</p>

        <button
          className="btn btn-wrong btn-reset-stats"
          onClick={() => setResetModal(true)}
        >
          <RotateCcw size={18} />
          <span>Сбросить статистику</span>
        </button>
      </div>

      <Modal
        isOpen={resetModal}
        onClose={() => setResetModal(false)}
        onConfirm={handleResetStats}
        title="Сбросить статистику?"
        message="Вы уверены, что хотите сбросить всю статистику? Это действие нельзя отменить. Колоды и карточки не будут удалены."
        confirmText="Сбросить"
        danger={true}
      />
    </div>
  );
};

export default Review;