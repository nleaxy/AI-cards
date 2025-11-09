import React, { useEffect, useState } from 'react';
import { BarChart3, Calendar, Award, TrendingUp } from 'lucide-react';

const Review = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error(err));
  }, []);

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

      <div className="stats-dashboard">
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <BarChart3 size={24} />
            <h3>Общий прогресс</h3>
          </div>
          <div className="dashboard-stats">
            <div className="dashboard-stat">
              <span className="stat-icon">📚</span>
              <div>
                <div className="stat-value">{stats.total_decks}</div>
                <div className="stat-label">Колод создано</div>
              </div>
            </div>
            <div className="dashboard-stat">
              <span className="stat-icon">✅</span>
              <div>
                <div className="stat-value">{stats.cards_studied}</div>
                <div className="stat-label">Карточек изучено</div>
              </div>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <Calendar size={24} />
            <h3>Активность</h3>
          </div>
          <div className="dashboard-stats">
            <div className="dashboard-stat">
              <span className="stat-icon">🔥</span>
              <div>
                <div className="stat-value">{stats.current_streak}</div>
                <div className="stat-label">Дней подряд</div>
              </div>
            </div>
            <div className="dashboard-stat">
              <span className="stat-icon">📅</span>
              <div>
                <div className="stat-value">5</div>
                <div className="stat-label">Дней на этой неделе</div>
              </div>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <Award size={24} />
            <h3>Достижения</h3>
          </div>
          <div className="achievements">
            <div className="achievement unlocked">
              <span className="achievement-icon">🎯</span>
              <div className="achievement-info">
                <div className="achievement-name">Первые шаги</div>
                <div className="achievement-desc">Создайте первую колоду</div>
              </div>
            </div>
            <div className="achievement unlocked">
              <span className="achievement-icon">📖</span>
              <div className="achievement-info">
                <div className="achievement-name">Книжный червь</div>
                <div className="achievement-desc">Изучите 50 карточек</div>
              </div>
            </div>
            <div className="achievement locked">
              <span className="achievement-icon">🔒</span>
              <div className="achievement-info">
                <div className="achievement-name">Мастер памяти</div>
                <div className="achievement-desc">Серия из 20 правильных ответов</div>
              </div>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <TrendingUp size={24} />
            <h3>Тенденция</h3>
          </div>
          <div className="trend-chart">
            <div className="chart-placeholder">
              <p>📈 График прогресса появится после нескольких дней обучения</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Review;