import React, { useState, ChangeEvent, DragEvent, FormEvent } from 'react';
import { Upload, FileText, Loader } from 'lucide-react';
import { apiFetch } from '../api/client';

interface FileUploadProps {
  onUploadSuccess: (data: any) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<string>('summary');
  const [loading, setLoading] = useState<boolean>(false);
  const [dragActive, setDragActive] = useState<boolean>(false);

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
      } else {
        alert('Пожалуйста, загрузите PDF файл');
      }
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);

    try {
      const response = await apiFetch('/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json().catch(() => ({ error: 'Invalid response from server' }));

      if (response.ok && (data.cards || data.summary)) {
        onUploadSuccess(data);
      } else {
        const errorMessage = data.error || data.message || `Неизвестная ошибка (${response.status})`;
        alert(`Ошибка: ${errorMessage}`);
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      alert(`Ошибка соединения: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="mode-selector">
          <label className={`mode-option ${mode === 'summary' ? 'active' : ''}`}>
            <input
              type="radio"
              value="summary"
              checked={mode === 'summary'}
              onChange={(e) => setMode(e.target.value)}
            />
            <span>📚 С кратким обзором</span>
            <small>Сначала покажем основные концепции</small>
          </label>

          <label className={`mode-option ${mode === 'direct' ? 'active' : ''}`}>
            <input
              type="radio"
              value="direct"
              checked={mode === 'direct'}
              onChange={(e) => setMode(e.target.value)}
            />
            <span>⚡ Сразу к карточкам</span>
            <small>Вы уже знакомы с материалом</small>
          </label>
        </div>

        <div
          className={`dropzone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            accept=".pdf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          {!file ? (
            <>
              <Upload size={48} className="upload-icon" />
              <h3>Перетащите PDF сюда</h3>
              <p>или</p>
              <label htmlFor="file-upload" className="btn btn-secondary">
                Выберите файл
              </label>
              <small className="file-hint">Максимум 16 МБ</small>
            </>
          ) : (
            <>
              <FileText size={48} className="file-icon" />
              <h3>{file.name}</h3>
              <p>{(file.size / 1024 / 1024).toFixed(2)} МБ</p>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setFile(null)}
              >
                Изменить файл
              </button>
            </>
          )}
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-large"
          disabled={!file || loading}
        >
          {loading ? (
            <>
              <Loader size={20} className="spinner" />
              <span>Обработка...</span>
            </>
          ) : (
            <>
              <span>Создать карточки</span>
              <span className="btn-arrow">→</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default FileUpload;