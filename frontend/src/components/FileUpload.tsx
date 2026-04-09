import React, { useState, ChangeEvent, DragEvent, FormEvent } from 'react';
import { Upload, FileText, Loader, AlertCircle } from 'lucide-react';
import { apiFetch } from '../api/client';

interface FileUploadProps {
  onUploadSuccess: (data: any) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<string>('summary');
  const [loading, setLoading] = useState<boolean>(false);
  const [dragActive, setDragActive] = useState<boolean>(false);
  // Состояние ошибки вместо alert() — graceful degradation
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [emptyResult, setEmptyResult] = useState<boolean>(false);

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setUploadError(null);
    setEmptyResult(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
      } else {
        setUploadError('Пожалуйста, загрузите файл в формате PDF');
      }
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    setEmptyResult(false);
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setUploadError(null);
    setEmptyResult(false);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);

    try {
      const response = await apiFetch('/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json().catch(() => ({ error: 'Сервер вернул неожиданный ответ' }));

      if (response.ok && (data.cards || data.summary)) {
        // Проверяем что карточки действительно есть
        if (data.cards && data.cards.length === 0) {
          setEmptyResult(true);
        } else {
          onUploadSuccess(data);
        }
      } else if (response.status >= 500 || response.status === 0) {
        // Сбой сервера или сети — graceful degradation
        setUploadError(
          'Сервис генерации временно недоступен. Вы можете добавить карточки вручную в разделе «Управление карточками».'
        );
      } else if (response.status === 408 || data.error?.includes('время')) {
        setUploadError('Превышено время ожидания ответа от ИИ. Попробуйте снова или используйте меньший файл.');
      } else {
        const errorMessage = data.error || data.message || `Неизвестная ошибка (${response.status})`;
        setUploadError(`Ошибка: ${errorMessage}`);
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      // Сетевая ошибка — деградированный режим
      setUploadError(
        'Не удалось связаться с сервером. Проверьте соединение или попробуйте позже. Карточки можно добавить вручную.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      {/* Блок ошибки — показывается вместо alert() */}
      {uploadError && (
        <div
          className="upload-error-block"
          role="alert"
          aria-live="assertive"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '12px',
            padding: '16px 20px',
            marginBottom: '20px',
            color: 'var(--danger, #ef4444)',
          }}
        >
          <AlertCircle size={22} style={{ flexShrink: 0, marginTop: 1 }} />
          <div>
            <strong style={{ display: 'block', marginBottom: 4 }}>Не удалось создать карточки</strong>
            <span style={{ fontSize: '0.9em', opacity: 0.9 }}>{uploadError}</span>
          </div>
        </div>
      )}

      {/* Блок пустого результата */}
      {emptyResult && (
        <div
          role="alert"
          aria-live="polite"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
            background: 'rgba(234, 179, 8, 0.12)',
            border: '1px solid rgba(234, 179, 8, 0.4)',
            borderRadius: '12px',
            padding: '16px 20px',
            marginBottom: '20px',
            color: '#ca8a04',
          }}
        >
          <AlertCircle size={22} style={{ flexShrink: 0, marginTop: 1 }} />
          <div>
            <strong style={{ display: 'block', marginBottom: 4 }}>Карточки не найдены</strong>
            <span style={{ fontSize: '0.9em' }}>
              ИИ не смог извлечь учебные концепции из этого текста. Попробуйте другой документ или добавьте карточки вручную.
            </span>
          </div>
        </div>
      )}

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
          role="region"
          aria-label="Область для загрузки PDF-файла"
        >
          <input
            type="file"
            id="file-upload"
            accept=".pdf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            aria-label="Выберите PDF файл"
          />

          {!file ? (
            <>
              <Upload size={48} className="upload-icon" aria-hidden="true" />
              <h3>Перетащите PDF сюда</h3>
              <p>или</p>
              <label htmlFor="file-upload" className="btn btn-secondary">
                Выберите файл
              </label>
              <small className="file-hint">Максимум 16 МБ</small>
            </>
          ) : (
            <>
              <FileText size={48} className="file-icon" aria-hidden="true" />
              <h3>{file.name}</h3>
              <p>{(file.size / 1024 / 1024).toFixed(2)} МБ</p>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => { setFile(null); setUploadError(null); setEmptyResult(false); }}
              >
                Изменить файл
              </button>
            </>
          )}
        </div>

        <button
          id="upload-submit-btn"
          type="submit"
          className="btn btn-primary btn-large"
          disabled={!file || loading}
          aria-busy={loading}
        >
          {loading ? (
            <>
              <Loader size={20} className="spinner" aria-hidden="true" />
              <span>Обработка...</span>
            </>
          ) : (
            <>
              <span>Создать карточки</span>
              <span className="btn-arrow" aria-hidden="true">→</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default FileUpload;