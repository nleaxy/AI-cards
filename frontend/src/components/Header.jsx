import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BookOpen, Upload, BarChart3 } from 'lucide-react';

const Header = () => {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  return (
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
            to="/review" 
            className={`nav-link ${isActive('/review') ? 'active' : ''}`}
          >
            <BarChart3 size={20} />
            <span>Статистика</span>
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;