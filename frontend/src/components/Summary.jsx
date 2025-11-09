import React from 'react';
import { BookOpen, ArrowRight } from 'lucide-react';

const Summary = ({ summaryData, onStartLearning }) => {
  return (
    <div className="summary-container">
      <div className="summary-header">
        <BookOpen size={32} className="summary-icon" />
        <h2>Краткий обзор материала</h2>
        <p>Ознакомьтесь с основными темами перед началом</p>
      </div>

      <div className="summary-sections">
        {summaryData.map((section, index) => (
          <div key={index} className="summary-card">
            <div className="summary-card-header">
              <span className="summary-number">{index + 1}</span>
              <h3>{section.title}</h3>
            </div>
            <p className="summary-content">{section.content}</p>
            <span className="summary-source">{section.source}</span>
          </div>
        ))}
      </div>

      <button className="btn btn-primary btn-large" onClick={onStartLearning}>
        <span>Начать изучение</span>
        <ArrowRight size={20} />
      </button>
    </div>
  );
};

export default Summary;