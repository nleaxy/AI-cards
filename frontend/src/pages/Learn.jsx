import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import ProgressBar from '../components/ProgressBar';
import { Trophy, RotateCcw, Keyboard } from 'lucide-react';

const Learn = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [cards, setCards] = useState([]);
  const [deckId, setDeckId] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [streak, setStreak] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [cardResults, setCardResults] = useState([]);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showHint, setShowHint] = useState(true);
  
  // Для отслеживания уникальных карточек в текущей сессии
  const streakCardsRef = useRef(new Set());

  useEffect(() => {
    const loadDeck = async () => {
      const pathDeckId = window.location.pathname.split('/').pop();
      
      if (location.state?.cards && location.state.cards.length > 0) {
        setCards(location.state.cards);
        setDeckId(pathDeckId);
      } else {
        try {
          const response = await fetch(`http://localhost:5000/api/decks/${pathDeckId}`);
          const data = await response.json();
          setCards(data.cards || []);
          setDeckId(pathDeckId);
        } catch (error) {
          console.error('Error loading deck:', error);
          navigate('/decks');
        }
      }
    };

    loadDeck();
  }, [location.state, navigate]);

  // Горячие клавиши
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Игнорируем если фокус в input/textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      if (completed) return;

      // Пробел - перевернуть карточку
      if (e.code === 'Space') {
        e.preventDefault();
        if (!isFlipped) {
          setIsFlipped(true);
        }
      }

      // Только если карточка перевёрнута
      if (isFlipped) {
        // ArrowLeft или 0 - неправильный ответ
        if (e.key === 'ArrowLeft' || e.key === '0') {
          e.preventDefault();
          handleAnswer(false);
        }
        // ArrowRight или 1 - правильный ответ
        if (e.key === 'ArrowRight' || e.key === '1') {
          e.preventDefault();
          handleAnswer(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isFlipped, completed, currentIndex, streak]);

  // Скрываем подсказку через 10 секунд
  useEffect(() => {
    const timer = setTimeout(() => setShowHint(false), 10000);
    return () => clearTimeout(timer);
  }, []);

  const handleAnswer = (correct) => {
    const currentCard = cards[currentIndex];
    let isStreakCard = false;
    let resetStreak = false;

    if (correct) {
      // Проверяем уникальность карточки для серии
      if (!streakCardsRef.current.has(currentCard.id)) {
        streakCardsRef.current.add(currentCard.id);
        setStreak(prev => prev + 1);
        isStreakCard = true;
      }
      setCorrectCount(prev => prev + 1);
    } else {
      // Сбрасываем серию и очищаем набор уникальных карточек
      setStreak(0);
      streakCardsRef.current.clear();
      resetStreak = true;
    }

    // Сохраняем результат
    setCardResults(prev => [...prev, {
      card_id: currentCard.id,
      correct: correct,
      is_streak_card: isStreakCard,
      reset_streak: resetStreak
    }]);

    // Сбрасываем состояние перелистывания
    setIsFlipped(false);

    if (currentIndex + 1 < cards.length) {
      setCurrentIndex(prev => prev + 1);
    } else {
      // Отправляем статистику на сервер
      saveSession();
      setCompleted(true);
    }
  };

  const saveSession = async () => {
    try {
      await fetch('http://localhost:5000/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deck_id: deckId,
          cards_studied: cards.length,
          cards_correct: correctCount,
          card_results: cardResults
        })
      });
    } catch (error) {
      console.error('Error saving session:', error);
    }
  };

  const handleRestart = () => {
    setCurrentIndex(0);
    setStreak(0);
    streakCardsRef.current.clear();
    setCompleted(false);
    setCorrectCount(0);
    setCardResults([]);
    setIsFlipped(false);
  };

  if (cards.length === 0) {
    return (
      <div className="container">
        <div className="loading">Загрузка карточек...</div>
      </div>
    );
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
              <span className="stat-value">{cardResults.filter(r => r.is_streak_card).length}</span>
              <span className="stat-label">Новых в серии</span>
            </div>
          </div>

          <div className="completion-actions">
            <button className="btn btn-secondary" onClick={handleRestart}>
              <RotateCcw size={20} />
              <span>Повторить</span>
            </button>
            <button className="btn btn-primary" onClick={() => navigate('/decks')}>
              <span>К колодам</span>
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
      
      {showHint && (
        <div className="keyboard-hint">
          <Keyboard size={18} />
          <div className="hint-keys">
            <div className="key">
              <span>Space</span>
              <small>Перевернуть</small>
            </div>
            <div className="key">
              <span>← или 0</span>
              <small>Нет</small>
            </div>
            <div className="key">
              <span>→ или 1</span>
              <small>Да</small>
            </div>
          </div>
        </div>
      )}

      <Card
        card={cards[currentIndex]}
        onAnswer={handleAnswer}
        isFlipped={isFlipped}
        setIsFlipped={setIsFlipped}
      />
    </div>
  );
};

export default Learn;