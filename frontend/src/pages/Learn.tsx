import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import CardItem from '../components/Card';
import ProgressBar from '../components/ProgressBar';
import { Trophy, RotateCcw, Keyboard } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../api/client';

interface CardData {
  id: string;
  question: string;
  answer: string;
  source?: string;
}

interface CardResult {
  card_id: string;
  correct: boolean;
  is_streak_card: boolean;
  reset_streak: boolean;
}

const Learn: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [cards, setCards] = useState<CardData[]>([]);
  const [deckId, setDeckId] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [streak, setStreak] = useState<number>(0);
  const [completed, setCompleted] = useState<boolean>(false);
  const [correctCount, setCorrectCount] = useState<number>(0);
  const [cardResults, setCardResults] = useState<CardResult[]>([]);
  const [isFlipped, setIsFlipped] = useState<boolean>(false);
  const [showHint, setShowHint] = useState<boolean>(true);

  // Для отслеживания уникальных карточек в текущей сессии
  const streakCardsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const loadDeck = async () => {
      const pathDeckId = window.location.pathname.split('/').pop();

      if (location.state?.cards && location.state.cards.length > 0) {
        setCards(location.state.cards);
        setDeckId(pathDeckId || null);
      } else {
        try {
          const response = await apiFetch(`/decks/${pathDeckId}`);
          const data = await response.json();
          setCards(data.cards || []);
          setDeckId(pathDeckId || null);
        } catch (error) {
          console.error('Error loading deck:', error);
          navigate('/decks');
        }
      }
    };

    loadDeck();
  }, [location.state, navigate, token]);

  // Горячие клавиши
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Игнорируем если фокус в input/textarea
      if (e.target instanceof HTMLElement && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
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

  const handleAnswer = (correct: boolean) => {
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
    const newResult = {
      card_id: currentCard.id,
      correct: correct,
      is_streak_card: isStreakCard,
      reset_streak: resetStreak
    };

    const updatedResults = [...cardResults, newResult];
    setCardResults(updatedResults);

    // Сбрасываем состояние перелистывания
    setIsFlipped(false);

    if (currentIndex + 1 < cards.length) {
      setCurrentIndex(prev => prev + 1);
    } else {
      // Отправляем статистику на сервер
      saveSession(updatedResults, correct ? correctCount + 1 : correctCount);
      setCompleted(true);
    }
  };

  const saveSession = async (results: CardResult[], finalCorrectCount: number) => {
    try {
      await apiFetch('/sessions', {
        method: 'POST',
        body: JSON.stringify({
          deck_id: deckId,
          cards_studied: cards.length,
          cards_correct: finalCorrectCount,
          card_results: results
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

      <CardItem
        card={cards[currentIndex]}
        onAnswer={handleAnswer}
        isFlipped={isFlipped}
        setIsFlipped={setIsFlipped}
      />
    </div>
  );
};

export default Learn;