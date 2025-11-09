import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import ProgressBar from '../components/ProgressBar';
import { Trophy, RotateCcw } from 'lucide-react';

const Learn = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [cards, setCards] = useState(location.state?.cards || []);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [streak, setStreak] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);

  useEffect(() => {
    if (!location.state?.cards) {
      navigate('/upload');
    }
  }, [location.state, navigate]);

  const handleAnswer = (correct) => {
    if (correct) {
      setStreak(prev => prev + 1);
      setCorrectCount(prev => prev + 1);
    } else {
      setStreak(0);
    }

    if (currentIndex + 1 < cards.length) {
      setCurrentIndex(prev => prev + 1);
    } else {
      setCompleted(true);
    }
  };

  const handleRestart = () => {
    setCurrentIndex(0);
    setStreak(0);
    setCompleted(false);
    setCorrectCount(0);
  };

  if (cards.length === 0) {
    return null;
  }

  if (completed) {
    const accuracy = Math.round((correctCount / cards.length) * 100);
    
    return (
      <div className="container page-learn">
        <div className="completion-screen">
          <Trophy size={80} className="trophy-icon" />
          <h1>Отличная работа! 🎉</h1>
          <p className="completion-message">
            Вы завершили изучение колоды
          </p>
          
          <div className="completion-stats">
            <div className="completion-stat">
              <span className="stat-value">{cards.length}</span>
              <span className="stat-label">Карточек пройдено</span>
            </div>
            <div className="completion-stat">
              <span className="stat-value">{accuracy}%</span>
              <span className="stat-label">Точность</span>
            </div>
            <div className="completion-stat">
              <span className="stat-value">{streak}</span>
              <span className="stat-label">Макс. серия</span>
            </div>
          </div>

          <div className="completion-actions">
            <button className="btn btn-secondary" onClick={handleRestart}>
              <RotateCcw size={20} />
              <span>Повторить</span>
            </button>
            <button className="btn btn-primary" onClick={() => navigate('/')}>
              <span>На главную</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container page-learn">
      <ProgressBar
        current={currentIndex + 1}
        total={cards.length}
        streak={streak}
      />
      
      <Card
        card={cards[currentIndex]}
        onAnswer={handleAnswer}
      />

      <div className="learn-footer">
        <p className="learn-hint">
          💡 Читайте вопрос внимательно, затем переверните карточку
        </p>
      </div>
    </div>
  );
};

export default Learn;