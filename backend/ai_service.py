import requests
import json
import re
import time
from typing import Optional
from config import Config


# --- Helper Functions ---

def _call_api_with_retry(payload: dict, max_retries: int = 3) -> dict:
    """
    Performs a POST request to the OpenRouter API with retry logic.

    Handles:
    - 429 Too Many Requests (rate limit): waits for Retry-After header or applies exponential backoff.
    - 5xx Server Errors (temporary server issue): retries after a delay.
    - Network errors (RequestException): retries.

    Args:
        payload: The request body payload for the API.
        max_retries: The maximum number of retry attempts (excluding the initial request).

    Returns:
        dict: A dictionary containing 'data' (API response) or 'error' (error message).
    """
    headers = {
        "Authorization": f"Bearer {Config.API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Study Cards Generator",
    }

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                url=Config.OPENROUTER_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )

            # Rate limit - use Retry-After if available, otherwise fall back to exponential backoff
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                print(f"[ai_service] Rate limited (429). Waiting {retry_after}s before retry {attempt+1}/{max_retries}")
                if attempt < max_retries:
                    time.sleep(min(retry_after, 30))
                    continue
                return {"error": "Превышен лимит запросов к API ИИ. Попробуйте через несколько минут."}

            # Temporary server error - retry
            if response.status_code >= 500:
                wait = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                print(f"[ai_service] Server error {response.status_code}. Waiting {wait}s, attempt {attempt+1}/{max_retries}")
                if attempt < max_retries:
                    time.sleep(wait)
                    continue
                return {"error": f"Сервис AI временно недоступен (HTTP {response.status_code}). Попробуйте позже."}

            if response.status_code != 200:
                return {"error": f"Ошибка API: {response.status_code} — {response.text[:200]}"}

            return {"data": response.json()}

        except requests.exceptions.Timeout:
            last_error = "Превышено время ожидания ответа от API"
            print(f"[ai_service] Timeout on attempt {attempt+1}/{max_retries}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue

        except requests.exceptions.ConnectionError as e:
            last_error = f"Ошибка подключения к API: {str(e)[:100]}"
            print(f"[ai_service] ConnectionError on attempt {attempt+1}: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue

        except requests.exceptions.RequestException as e:
            last_error = f"Ошибка запроса к API: {str(e)[:100]}"
            break

    return {"error": last_error or "Неизвестная ошибка при обращении к API"}


def _parse_json_response(raw: str) -> Optional[list]:
    """Parses JSON from the API response, stripping any markdown code block wrappers."""
    # Strip markdown code blocks
    content = raw.strip()
    if content.startswith('```json'):
        content = content[7:]
    if content.startswith('```'):
        content = content[3:]
    if content.endswith('```'):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[ai_service] JSON parse error: {e}")
        # Attempt to repair unescaped backslashes (e.g., in LaTeX formulas)
        try:
            fixed = re.sub(r'\\(?![/u"\\bfnrt])', r'\\\\', content)
            result = json.loads(fixed)
            print("[ai_service] JSON repaired successfully")
            return result
        except Exception as e2:
            print(f"[ai_service] Failed to repair JSON: {e2}")
            print(f"[ai_service] Content snippet: {content[:300]}")
            return None


# --- Public API ---

def generate_cards_from_text(text: str, mode: str = 'summary') -> dict:
    """
    Generates study cards from the provided text using AI (OpenRouter).

    Args:
        text: Input text to analyze.
        mode: 'summary' (generate cards + overview) or 'direct' (generate cards only).

    Returns:
        dict: {'success': True, 'cards': [...], 'total_cards': int} or {'error': str}.
    """
    if not Config.API_KEY:
        return {"error": "API_KEY is not configured on the server"}

    if not text or not text.strip():
        return {"error": "Text cannot be empty"}

    # Limit input text size (~30k characters ≈ 8k tokens)
    max_chars = 30000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."

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

    cards_payload = {
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
    }

    api_result = _call_api_with_retry(cards_payload)
    if "error" in api_result:
        return api_result

    data = api_result.get("data", {})
    if "choices" not in data or not data["choices"]:
        error_msg = data.get("error", {}).get("message", "API вернул пустой или некорректный ответ")
        return {"error": f"Ошибка AI: {error_msg}"}

    cards_raw = data["choices"][0]["message"]["content"]
    cards = _parse_json_response(cards_raw)

    if cards is None:
        return {"error": "Не удалось распарсить ответ AI. Попробуйте снова."}

    # Assign sequential IDs to each card
    for idx, card in enumerate(cards):
        card['id'] = idx + 1

    result = {
        "success": True,
        "cards": cards,
        "total_cards": len(cards)
    }

    # Summary mode - generate a brief topic overview in addition to cards
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

        summary_payload = {
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
        }

        summary_api = _call_api_with_retry(summary_payload)
        if "data" in summary_api and "choices" in summary_api["data"] and summary_api["data"]["choices"]:
            summary_raw = summary_api["data"]["choices"][0]["message"]["content"]
            summary = _parse_json_response(summary_raw)
            if summary:
                result['summary'] = summary
            else:
                result['summary'] = [{
                    "title": "Обзор материала",
                    "content": "Материал успешно обработан и готов к изучению",
                    "source": "Весь документ"
                }]
        else:
            # Summary generation failure is non-critical - cards were already created
            result['summary'] = [{
                "title": "Обзор недоступен",
                "content": "Не удалось сгенерировать обзор, но карточки созданы успешно",
                "source": "Весь документ"
            }]

    return result


def get_mock_stats():
    """Mock statistics endpoint (to be replaced with actual database data)."""
    return {
        'total_decks': 0,
        'cards_studied': 0,
        'current_streak': 0
    }