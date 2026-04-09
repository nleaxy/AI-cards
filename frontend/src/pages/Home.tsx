import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, BookOpen, Target, Zap } from 'lucide-react';
import SEO from '../components/SEO';

// JSON-LD разметка (schema.org/SoftwareApplication) — для структурированных данных в поиске
const JSON_LD = JSON.stringify({
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'AI Cards',
  description:
    'Сервис автоматической генерации учебных карточек из PDF-документов с помощью искусственного интеллекта.',
  applicationCategory: 'EducationApplication',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'RUB',
  },
  featureList: [
    'Загрузка PDF и автоматическое создание карточек',
    'Режим обучения с интервальным повторением',
    'Отслеживание прогресса и статистики',
    'Экспорт карточек в формат CSV (Anki)',
  ],
});

const Home: React.FC = () => {
  const navigate = useNavigate();

  return (
    <>
      <SEO
        canonical="/"
        description="Загрузите PDF-конспект и получите готовые учебные карточки, созданные ИИ. Эффективное обучение с интервальным повторением."
      />

      {/* JSON-LD структурированные данные для поисковых роботов */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON_LD }}
      />

      <div className="container page-home">
        <section className="hero" aria-label="Главный блок">
          <div className="hero-content">
            {/* h1 — один на странице, описывает суть сервиса */}
            <h1 className="hero-title">
              Превратите конспекты
              <span className="gradient-text"> в знания</span>
            </h1>
            <p className="hero-subtitle">
              Загрузите PDF — получите готовые карточки для эффективного обучения с помощью ИИ
            </p>
            <button
              id="hero-cta-btn"
              className="btn btn-primary btn-large"
              onClick={() => navigate('/upload')}
              aria-label="Перейти к загрузке PDF и созданию карточек"
            >
              <Plus size={20} aria-hidden="true" />
              <span>Создать карточки</span>
            </button>
          </div>

          <div className="hero-illustration" aria-hidden="true">
            <div className="floating-card card-1">
              <BookOpen size={32} />
            </div>
            <div className="floating-card card-2">
              <Target size={32} />
            </div>
            <div className="floating-card card-3">
              <Zap size={32} />
            </div>
          </div>
        </section>

        <section className="features" aria-label="Как работает сервис">
          <h2>Как это работает</h2>
          <div className="features-grid">
            <article className="feature-card">
              <div className="feature-icon" aria-hidden="true">📤</div>
              <h3>Загрузите PDF</h3>
              <p>Выберите конспект или учебный материал в формате PDF</p>
            </article>
            <article className="feature-card">
              <div className="feature-icon" aria-hidden="true">🤖</div>
              <h3>ИИ создаст карточки</h3>
              <p>Автоматический анализ текста и генерация вопросов с ответами</p>
            </article>
            <article className="feature-card">
              <div className="feature-icon" aria-hidden="true">🎯</div>
              <h3>Учитесь эффективно</h3>
              <p>Проходите карточки и отслеживайте свой прогресс</p>
            </article>
          </div>
        </section>
      </div>
    </>
  );
};

export default Home;