import React from 'react';
import { Helmet } from 'react-helmet-async';

interface SEOProps {
  title?: string;
  description?: string;
  canonical?: string;
  noIndex?: boolean;
  ogType?: string;
  ogImage?: string;
}

const BASE_TITLE = 'AI Cards — умные учебные карточки из PDF';
const BASE_DESCRIPTION =
  'Загрузите PDF-конспект и получите готовые учебные карточки, созданные искусственным интеллектом. Эффективное повторение, отслеживание прогресса.';
const BASE_URL = 'http://localhost:3000';
const OG_IMAGE = `${BASE_URL}/og-image.png`;

const SEO: React.FC<SEOProps> = ({
  title,
  description = BASE_DESCRIPTION,
  canonical,
  noIndex = false,
  ogType = 'website',
  ogImage = OG_IMAGE,
}) => {
  const fullTitle = title ? `${title} | AI Cards` : BASE_TITLE;
  const canonicalUrl = canonical ? `${BASE_URL}${canonical}` : undefined;

  return (
    <Helmet>
      {/* Основные мета-теги */}
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      {noIndex && <meta name="robots" content="noindex, nofollow" />}

      {/* Canonical URL */}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}

      {/* Open Graph / Social */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={ogType} />
      <meta property="og:image" content={ogImage} />
      {canonicalUrl && <meta property="og:url" content={canonicalUrl} />}
      <meta property="og:locale" content="ru_RU" />
      <meta property="og:site_name" content="AI Cards" />

      {/* Twitter Card */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
    </Helmet>
  );
};

export default SEO;
