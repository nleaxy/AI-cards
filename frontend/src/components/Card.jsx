import React, { useState, useEffect, useRef } from 'react';
import { RotateCcw } from 'lucide-react';

const Card = ({ card, onAnswer }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const [showAnswer, setShowAnswer] = useState(false);
  const [cardHeight, setCardHeight] = useState(0);
  const frontRef = useRef(null);
  const backRef = useRef(null);

  const calculateHeight = () => {
    const frontHeight = frontRef.current?.scrollHeight || 0;
    const backHeight = backRef.current?.scrollHeight || 0;
    const maxHeight = Math.max(frontHeight, backHeight);
    setCardHeight(maxHeight);
  };

  useEffect(() => {
    calculateHeight();
  }, [card]);

  useEffect(() => {
    window.addEventListener('resize', calculateHeight);
    return () => window.removeEventListener('resize', calculateHeight);
  }, []);

  const handleFlip = () => {
    setIsFlipped(true);
    setTimeout(() => setShowAnswer(true), 300);
  };

  const handleAnswer = (correct) => {
    setShowAnswer(false);
    setIsFlipped(false);
    setTimeout(() => onAnswer(correct), 300);
  };

  return (
    <div className="card-container">
      <div className={`flashcard ${isFlipped ? 'flipped' : ''}`} style={{ height: cardHeight ? `${cardHeight}px` : 'auto' }}>
        <div className="flashcard-inner" style={{ height: cardHeight ? `${cardHeight}px` : 'auto' }}>
          <div className="flashcard-front" ref={frontRef}>
            <span className="card-label">Вопрос</span>
            <h2>{card.question}</h2>
            <div style={{ marginTop: 'auto' }}>
              <button className="btn btn-secondary" onClick={handleFlip}>
                <RotateCcw size={18} />
                <span>Показать ответ</span>
              </button>
            </div>
          </div>

          <div className="flashcard-back" ref={backRef}>
            <span className="card-label">Ответ</span>
            <h2>{card.answer}</h2>
            <span className="card-source">{card.source}</span>
          </div>
        </div>
      </div>

      {showAnswer && (
        <div className="answer-buttons">
          <p className="answer-prompt">Вы ответили правильно?</p>
          <div className="button-group">
            <button className="btn btn-wrong" onClick={() => handleAnswer(false)}>❌ Нет</button>
            <button className="btn btn-correct" onClick={() => handleAnswer(true)}>✅ Да</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Card;