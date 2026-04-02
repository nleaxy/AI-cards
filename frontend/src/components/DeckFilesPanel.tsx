import React, { useState, useEffect } from 'react';
import { Download, Trash2, File as FileIcon, UploadCloud, AlertCircle } from 'lucide-react';
import { apiFetch } from '../api/client';

interface DeckFile {
    id: number;
    deck_id: number;
    original_name: string;
    size_bytes: number;
    mime_type: string;
    uploaded_at: string;
}

interface DeckFilesPanelProps {
    deckId: string;
}

const DeckFilesPanel: React.FC<DeckFilesPanelProps> = ({ deckId }) => {
    const [files, setFiles] = useState<DeckFile[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadFiles();
    }, [deckId]);

    const loadFiles = async () => {
        try {
            const response = await apiFetch(`/decks/${deckId}/files`);
            if (response.ok) {
                const data = await response.json();
                setFiles(data);
            }
        } catch (err) {
            console.error('Error loading files:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        // Общая клиентская валидация (до 10MB)
        if (selectedFile.size > 10 * 1024 * 1024) {
            setError('Файл слишком большой (макс 10 MB)');
            return;
        }

        const payload = new FormData();
        payload.append('file', selectedFile);

        setUploading(true);
        setError(null);
        try {
            const response = await apiFetch(`/decks/${deckId}/files`, {
                method: 'POST',
                body: payload,
            });

            if (response.ok) {
                await loadFiles();
                if (e.target) e.target.value = ''; // сброс инпута
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Ошибка при загрузке файла');
            }
        } catch (err) {
            setError('Сетевая ошибка при загрузке');
        } finally {
            setUploading(false);
        }
    };

    const handleDownloadFile = async (fileId: number, originalName: string) => {
        try {
            const response = await apiFetch(`/files/${fileId}/download`);
            if (response.ok) {
                const data = await response.json();
                // Используем presigned URL для скачивания (открываем в новом окне)
                const a = document.createElement('a');
                a.href = data.url;
                a.download = originalName;
                a.target = '_blank';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            } else {
                alert('Ошибка при получении ссылки на файл');
            }
        } catch (err) {
            console.error(err);
            alert('Ошибка соединения');
        }
    };

    const handleDeleteFile = async (fileId: number) => {
        if (!window.confirm('Удалить этот файл из хранилища?')) return;

        try {
            const response = await apiFetch(`/files/${fileId}`, {
                method: 'DELETE',
            });
            if (response.ok) {
                setFiles(files.filter((f) => f.id !== fileId));
            } else {
                alert('Ошибка при удалении');
            }
        } catch (err) {
            alert('Ошибка соединения');
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    };

    if (loading) return <div>Загрузка файлов...</div>;

    return (
        <div className="deck-files-panel" style={{ marginTop: '20px', padding: '20px', background: 'var(--card-bg)', borderRadius: '12px' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FileIcon size={20} /> Прикреплённые файлы (MinIO Object Storage)
            </h3>

            {error && (
                <div className="error-message" style={{ display: 'flex', gap: '10px', alignItems: 'center', margin: '15px 0', background: 'var(--wrong-color)', padding: '10px', borderRadius: '8px' }}>
                    <AlertCircle size={20} />
                    {error}
                </div>
            )}

            <div className="files-list" style={{ marginTop: '15px' }}>
                {files.length === 0 ? (
                    <p style={{ color: 'var(--text-light)' }}>К этой колоде не прикреплено файлов. Загрузите PDF, DOCX или изображения для дополнительного контекста.</p>
                ) : (
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                        {files.map(file => (
                            <li key={file.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', borderBottom: '1px solid var(--border-color)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <FileIcon size={16} />
                                    <span>{file.original_name}</span>
                                    <span style={{ color: 'var(--text-light)', fontSize: '0.85em' }}>({formatFileSize(file.size_bytes)})</span>
                                </div>
                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <button className="btn btn-secondary" onClick={() => handleDownloadFile(file.id, file.original_name)} title="Скачать файл">
                                        <Download size={16} />
                                    </button>
                                    <button className="btn btn-wrong" onClick={() => handleDeleteFile(file.id)} title="Удалить файл">
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            <div style={{ marginTop: '20px' }}>
                <input
                    type="file"
                    id="deck-file-upload"
                    style={{ display: 'none' }}
                    onChange={handleFileUpload}
                    disabled={uploading}
                />
                <label htmlFor="deck-file-upload" className={`btn btn-primary ${uploading ? 'disabled' : ''}`} style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                    <UploadCloud size={18} />
                    {uploading ? 'Загрузка...' : 'Загрузить файл'}
                </label>
            </div>
        </div>
    );
};

export default DeckFilesPanel;
