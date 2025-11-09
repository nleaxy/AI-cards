import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import Summary from '../components/Summary';

const Upload = () => {
  const [uploadData, setUploadData] = useState(null);
  const [showSummary, setShowSummary] = useState(false);
  const navigate = useNavigate();

  const handleUploadSuccess = (data) => {
    setUploadData(data);
    if (data.mode === 'summary') {
      setShowSummary(true);
    } else {
      navigate('/learn/1', { state: { cards: data.cards } });
    }
  };

  const handleStartLearning = () => {
    navigate('/learn/1', { state: { cards: uploadData.cards } });
  };

  return (
    <div className="container page-upload">
      {!showSummary ? (
        <>
          <div className="page-header">
            <h1>Загрузите материал</h1>
            <p>Выберите PDF файл с конспектом для создания карточек</p>
          </div>
          <FileUpload onUploadSuccess={handleUploadSuccess} />
        </>
      ) : (
        <Summary
          summaryData={uploadData.summary}
          onStartLearning={handleStartLearning}
        />
      )}
    </div>
  );
};

export default Upload;