import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { User, LogOut, Trash2, BarChart2, Calendar, Book, TrendingUp, RotateCcw } from 'lucide-react';
import ConfirmModal from '../components/ConfirmModal';

interface UserStats {
    total_decks: number;
    cards_studied: number;
    current_streak: number;
    max_streak: number;
}

const Profile: React.FC = () => {
    const { user, logout, token } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState<UserStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [logoutModalOpen, setLogoutModalOpen] = useState(false);
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [resetModalOpen, setResetModalOpen] = useState(false);
    const [error, setError] = useState<string>('');

    useEffect(() => {
        if (!user) {
            navigate('/');
            return;
        }
        fetchStats();
    }, [user, navigate]);

    const fetchStats = async () => {
        try {
            const headers: HeadersInit = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            const response = await fetch('http://localhost:5000/api/stats', { headers });

            if (!response.ok) {
                throw new Error('Failed to fetch stats');
            }

            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Error fetching stats:', error);
            setError('Не удалось загрузить статистику');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const handleDeleteAccount = async () => {
        try {
            if (!token) {
                setError('Вы не авторизованы. Пожалуйста, войдите в аккаунт.');
                return;
            }

            const response = await fetch('http://localhost:5000/api/auth/user', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json().catch(() => ({}));

            if (response.ok) {
                logout();
                navigate('/');
            } else {
                const errorMsg = data.error || data.message || `Ошибка ${response.status}: ${response.statusText}`;
                setError(errorMsg);
                console.error('Delete account error:', { response: response.status, data });
            }
        } catch (error: any) {
            console.error('Error deleting account:', error);
            setError(`Ошибка соединения: ${error.message}`);
        }
    };

    const handleResetStats = async () => {
        try {
            if (!token) return;
            const response = await fetch('http://localhost:5000/api/stats/reset', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                fetchStats(); // Reload stats
                setResetModalOpen(false);
            } else {
                setError('Не удалось сбросить статистику');
            }
        } catch (error) {
            setError('Ошибка соединения');
        }
    };

    if (loading) {
        return <div className="container"><div className="loading">Загрузка профиля...</div></div>;
    }

    return (
        <div className="container page-profile">
            <div className="profile-header">
                <div className="profile-avatar">
                    <User size={64} />
                </div>
                <h1>{user?.username}</h1>
                <p className="profile-email">{user?.email}</p>
            </div>

            {error && (
                <div className="error-message" style={{ textAlign: 'center', marginBottom: '2rem', color: 'var(--danger)' }}>
                    {error}
                </div>
            )}

            <div className="stats-grid-enhanced">
                <div className="stat-card-enhanced stat-card-primary">
                    <div className="stat-icon-large">
                        <Book size={40} />
                    </div>
                    <div className="stat-value-large">{stats?.total_decks || 0}</div>
                    <div className="stat-label-large">Колод создано</div>
                </div>

                <div className="stat-card-enhanced stat-card-success">
                    <div className="stat-icon-large">
                        <BarChart2 size={40} />
                    </div>
                    <div className="stat-value-large">{stats?.cards_studied || 0}</div>
                    <div className="stat-label-large">Карточек изучено</div>
                </div>

                <div className="stat-card-enhanced stat-card-warning">
                    <div className="stat-icon-large">
                        <Calendar size={40} />
                    </div>
                    <div className="stat-value-large">{stats?.current_streak || 0}</div>
                    <div className="stat-label-large">Текущая серия</div>
                </div>

                <div className="stat-card-enhanced stat-card-secondary">
                    <div className="stat-icon-large">
                        <TrendingUp size={40} />
                    </div>
                    <div className="stat-value-large">{stats?.max_streak || 0}</div>
                    <div className="stat-label-large">Лучшая серия</div>
                </div>
            </div>

            <div className="profile-actions">
                <button onClick={() => setDeleteModalOpen(true)} className="btn btn-wrong btn-large">
                    <Trash2 size={17} />
                    <span>Удалить аккаунт</span>
                </button>
                <button onClick={() => setResetModalOpen(true)} className="btn btn-warning btn-large">
                    <RotateCcw size={17} />
                    <span>Сбросить статистику</span>
                </button>
                <button onClick={() => setLogoutModalOpen(true)} className="btn btn-blue btn-large">
                    <LogOut size={17} />
                    <span>Выйти из аккаунта</span>
                </button>
            </div>

            <ConfirmModal
                isOpen={resetModalOpen}
                onClose={() => setResetModalOpen(false)}
                onConfirm={handleResetStats}
                title="Сбросить статистику?"
                message="Вы уверены, что хотите сбросить всю статистику? Это действие обнулит счетчики изученных карточек и серий. Колоды не будут удалены."
                confirmText="Сбросить"
                cancelText="Отмена"
                variant="warning"
            />

            <ConfirmModal
                isOpen={logoutModalOpen}
                onClose={() => setLogoutModalOpen(false)}
                onConfirm={handleLogout}
                title="Выйти из аккаунта?"
                message="Вы уверены, что хотите выйти из аккаунта? Вам придется войти снова, чтобы получить доступ к своим колодам."
                confirmText="Выйти"
                cancelText="Отмена"
                variant="info"
            />

            <ConfirmModal
                isOpen={deleteModalOpen}
                onClose={() => setDeleteModalOpen(false)}
                onConfirm={handleDeleteAccount}
                title="Удалить аккаунт?"
                message="Вы уверены, что хотите удалить аккаунт? Это действие необратимо и удалит все ваши колоды, карточки и прогресс навсегда."
                confirmText="Удалить аккаунт"
                cancelText="Отмена"
                variant="danger"
            />
        </div>
    );
};

export default Profile;
