import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { BookOpen, Upload, Layers, LogIn, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthModal from './AuthModal';

const Header: React.FC = () => {
  const location = useLocation();
  const { user } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      <header className="header">
        <div className="container">
          <Link to="/" className="logo">
            <BookOpen size={32} />
            <span className="logo-text">Study Cards</span>
          </Link>

          <nav className="nav">
            <Link
              to="/"
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
            >
              <BookOpen size={20} />
              <span>Главная</span>
            </Link>
            <Link
              to="/upload"
              className={`nav-link ${isActive('/upload') ? 'active' : ''}`}
            >
              <Upload size={20} />
              <span>Загрузить</span>
            </Link>
            <Link
              to="/decks"
              className={`nav-link ${isActive('/decks') ? 'active' : ''}`}
            >
              <Layers size={20} />
              <span>Колоды</span>
            </Link>
          </nav>

          <div className="auth-controls">
            {user ? (
                <Link
                  to="/profile"
                  className={`user-menu-btn ${isActive('/profile') ? 'active' : ''}`}
                >
                <UserIcon size={20} />
                <span>{user.username}</span>
              </Link>
            ) : (
              <button
                className="btn btn-secondary"
                onClick={() => setIsAuthModalOpen(true)}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <LogIn size={20} />
                <span>Войти</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </>
  );
};

export default Header;