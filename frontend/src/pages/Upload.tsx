import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import Summary from '../components/Summary';

interface Card {
  question: string;
  answer: string;
  source?: string;
}

interface SummarySection {
  title: string;
  content: string;
  source?: string;
}

interface UploadData {
  mode: 'summary' | 'cards';
  cards?: Card[];
  summary?: SummarySection[];
  deck_id?: number;
}

const Upload: React.FC = () => {
  const [uploadData, setUploadData] = useState<UploadData | null>(null);
  const [showSummary, setShowSummary] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleUploadSuccess = (data: UploadData) => {
    setUploadData(data);
    if (data.mode === 'summary') {
      setShowSummary(true);
    } else {
      navigate(`/learn/${data.deck_id}`, { state: { cards: data.cards } });
    }
  };

  const handleStartLearning = () => {
    if (uploadData?.cards && uploadData?.deck_id) {
      navigate(`/learn/${uploadData.deck_id}`, { state: { cards: uploadData.cards } });
    }
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
        uploadData?.summary && (
          <Summary
            summaryData={uploadData.summary}
            onStartLearning={handleStartLearning}
          />
        )
      )}
    </div>
  );
};

export default Upload;