# маршруты для SEO-файлов: robots.txt и sitemap.xml
from flask import Blueprint, Response, jsonify
from datetime import datetime

seo_bp = Blueprint('seo', __name__)

# указываем поисковым роботам что индексировать
@seo_bp.route('/robots.txt', methods=['GET'])
def robots_txt():
    content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /decks
Disallow: /upload
Disallow: /learn/
Disallow: /manage/
Disallow: /review
Disallow: /profile
Disallow: /admin

# Sitemap location
Sitemap: http://localhost:5000/sitemap.xml
"""
    return Response(content, mimetype='text/plain')


# для поисковых роботов, перечисляем публичные страницы
@seo_bp.route('/sitemap.xml', methods=['GET'])
def sitemap_xml():
    lastmod = datetime.utcnow().strftime('%Y-%m-%d')
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>http://localhost:3000/</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    return Response(content, mimetype='application/xml')
