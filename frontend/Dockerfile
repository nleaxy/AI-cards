# Этап 1: Сборка
FROM node:18-alpine AS build

WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install --legacy-peer-deps

# Копируем исходный код
COPY . .

# Собираем приложение для production
RUN npm run build

# Этап 2: Раздача статики
FROM nginx:alpine

# Копируем собранные файлы из предыдущего этапа в директорию Nginx
COPY --from=build /app/build /usr/share/nginx/html

# Заменяем конфиг Nginx по умолчанию, чтобы корректно работал React Router
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
