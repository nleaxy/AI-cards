# Используем официальный образ Python на базе легковесного Alpine или slim
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости, необходимые для psycopg2 и других библиотек компиляции (если понадобится)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь исходный код приложения
COPY . .

# Создаем папку для загрузок на всякий случай
RUN mkdir -p uploads

# Указываем пользователя без root прав для безопасности (опционально, но хорошая практика)
# RUN useradd -m myuser
# USER myuser

# Открываем порт 5000
EXPOSE 5000

# Запускаем Gunicorn сервер вместо встроенного Flask сервера для продакшн-уровня
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]
