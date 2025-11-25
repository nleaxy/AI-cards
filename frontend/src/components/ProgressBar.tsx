import React from 'react';
import { Flame } from 'lucide-react';

interface ProgressBarProps {
  current: number;
  total: number;
  streak: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ current, total, streak }) => {
  const progress = (current / total) * 100;

  return (
    <div className="progress-container">
      <div className="progress-info">
        <span className="progress-text">
          {current} / {total} карточек
        </span>
        {streak > 0 && (
          <div className="streak">
            <Flame size={18} className="flame-icon" />
            <span>{streak} подряд</span>
          </div>
        )}
      </div>
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;