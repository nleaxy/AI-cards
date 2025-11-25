import requests
import json
import re
from config import Config

def generate_cards_from_text(text, mode='summary'):
    """
    Генерация учебных карточек из текста с помощью AI
    
    Args:
        text (str): Текст для анализа
        mode (str): 'summary' - с кратким обзором, 'direct' - только карточки
    
    Returns:
        dict: Результат с карточками и опционально с обзором
    """
    if not Config.API_KEY:
        return {"error": "API_KEY не найден в переменных окружения"}
    
    if not text or not text.strip():
        return {"error": "Текст не может быть пустым"}
    
    try:
        # Ограничиваем текст для API (примерно 8000 токенов)
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        # Промпт для генерации карточек
        cards_prompt = f"""Проанализируй следующий учебный материал и создай учебные карточки.

Для каждой важной концепции создай:
1. Чёткий вопрос (на русском языке)
2. Краткий ответ (на русском языке)
3. Ссылку на источник (укажи страницу или раздел)

Создай минимум 5 и максимум 15 карточек.

ВАЖНО: Верни ТОЛЬКО валидный JSON массив без каких-либо дополнительных пояснений или markdown разметки.
Формат:
[
    {{
        "question": "Что такое X?",
        "answer": "X - это...",
        "source": "Страница 1"
    }}
]

Текст для анализа:
{text}"""

        # Запрос к API для карточек
        cards_response = requests.post(
            url=Config.OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {Config.API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Study Cards Generator",
            },
            data=json.dumps({
                "model": Config.MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - эксперт по созданию учебных материалов. Создаёшь качественные вопросы и ответы для запоминания информации. Всегда отвечаешь ТОЛЬКО валидным JSON без дополнительного текста."
                    },
                    {
                        "role": "user",
                        "content": cards_prompt
                    }
                ],
                "temperature": 0.7,
            }),
            timeout=60
        )
        
        if cards_response.status_code != 200:
            return {"error": f"Ошибка API при генерации карточек: {cards_response.status_code} - {cards_response.text}"}
        
        cards_result = cards_response.json()
        cards_content = cards_result['choices'][0]['message']['content'].strip()
        
        # Очищаем от возможной markdown разметки
        if cards_content.startswith('```json'):
            cards_content = cards_content[7:]
        if cards_content.startswith('```'):
            cards_content = cards_content[3:]
        if cards_content.endswith('```'):
            cards_content = cards_content[:-3]
        cards_content = cards_content.strip()
        
        # Парсим JSON
        try:
            cards = json.loads(cards_content)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            # Попытка исправить распространенные ошибки экранирования (например, в LaTeX)
            try:
                # Находим обратные слеши, за которыми НЕ следует валидный управляющий символ
                # Валидные: " \ / b f n r t u
                fixed_content = re.sub(r'\\(?![/u"\\bfnrt])', r'\\\\', cards_content)
                cards = json.loads(fixed_content)
                print("JSON repaired successfully")
            except Exception as e2:
                print(f"Failed to repair JSON: {e2}")
                print(f"Content: {cards_content[:500]}")
                return {"error": f"Не удалось распарсить ответ AI: {str(e)}"}
        
        # Добавляем ID к карточкам
        for idx, card in enumerate(cards):
            card['id'] = idx + 1
        
        result = {
            "success": True,
            "cards": cards,
            "total_cards": len(cards)
        }
        
        # Если режим с обзором - генерируем краткую сводку
        if mode == 'summary':
            summary_prompt = f"""Проанализируй следующий учебный материал и создай краткий обзор основных тем.

Создай 2-4 блока, каждый с:
1. Заголовком темы
2. Кратким описанием (1-2 предложения)
3. Ссылкой на источник

ВАЖНО: Верни ТОЛЬКО валидный JSON массив без дополнительных пояснений.
Формат:
[
    {{
        "title": "Название темы",
        "content": "Краткое описание темы",
        "source": "Страницы 1-3"
    }}
]

Текст:
{text[:10000]}"""

            summary_response = requests.post(
                url=Config.OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {Config.API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "Study Cards Generator",
                },
                data=json.dumps({
                    "model": Config.MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты - эксперт по созданию учебных обзоров. Создаёшь краткие и информативные сводки. Всегда отвечаешь ТОЛЬКО валидным JSON без дополнительного текста."
                        },
                        {
                            "role": "user",
                            "content": summary_prompt
                        }
                    ],
                    "temperature": 0.7,
                }),
                timeout=60
            )
            
            if summary_response.status_code == 200:
                summary_result = summary_response.json()
                summary_content = summary_result['choices'][0]['message']['content'].strip()
                
                # Очищаем от markdown
                if summary_content.startswith('```json'):
                    summary_content = summary_content[7:]
                if summary_content.startswith('```'):
                    summary_content = summary_content[3:]
                if summary_content.endswith('```'):
                    summary_content = summary_content[:-3]
                summary_content = summary_content.strip()
                
                try:
                    summary = json.loads(summary_content)
                    result['summary'] = summary
                except json.JSONDecodeError:
                    # Если не получилось распарсить обзор - не критично
                    result['summary'] = [
                        {
                            "title": "Обзор материала",
                            "content": "Материал успешно обработан и готов к изучению",
                            "source": "Весь документ"
                        }
                    ]
        
        return result
        
    except requests.exceptions.Timeout:
        return {"error": "Превышено время ожидания ответа от API"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Ошибка запроса к API: {str(e)}"}
    except Exception as e:
        return {"error": f"Произошла ошибка: {str(e)}"}


def get_mock_stats():
    """Заглушка для статистики (будет заменена на реальные данные из БД)"""
    return {
        'total_decks': 0,
        'cards_studied': 0,
        'current_streak': 0
    }