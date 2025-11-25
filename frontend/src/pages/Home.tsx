import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, BookOpen, Target, Zap } from 'lucide-react';

interface Stats {
  total_decks: number;
  cards_studied: number;
  max_streak: number;
}

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="container page-home">
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            Превратите конспекты
            <span className="gradient-text"> в знания</span>
          </h1>
          <p className="hero-subtitle">
            Загрузите PDF — получите готовые карточки для эффективного обучения
          </p>
          <button
            className="btn btn-primary btn-large"
            onClick={() => navigate('/upload')}
          >
            <Plus size={20} />
            <span>Создать карточки</span>
          </button>
        </div>

        <div className="hero-illustration">
          <div className="floating-card card-1">
            <BookOpen size={32} />
          </div>
          <div className="floating-card card-2">
            <Target size={32} />
          </div>
          <div className="floating-card card-3">
            <Zap size={32} />
          </div>
        </div>
      </section>

      {/* {stats && (
        <section className="stats-section">
          <h2>Ваш прогресс</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">📚</div>
              <div className="stat-value">{stats.total_decks}</div>
              <div className="stat-label">Колод создано</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-value">{stats.cards_studied}</div>
              <div className="stat-label">Карточек изучено</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🔥</div>
              <div className="stat-value">{stats.max_streak}</div>
              <div className="stat-label">Макс. серия верных</div>
            </div>
          </div>
        </section>
      )} */}

      <section className="features">
        <h2>Как это работает</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📤</div>
            <h3>Загрузите PDF</h3>
            <p>Выберите конспект или учебный материал</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>ИИ создаст карточки</h3>
            <p>Автоматический анализ и генерация вопросов</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>Учитесь эффективно</h3>
            <p>Проходите карточки и отслеживайте прогресс</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;