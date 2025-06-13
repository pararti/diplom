# Многоступенчатая сборка для Vue.js приложения
FROM node:18-alpine AS build-stage

# Установка рабочей директории
WORKDIR /app

# Копирование package.json
COPY package.json ./

# Установка зависимостей (включая dev dependencies для сборки)
RUN npm install

# Копирование исходного кода
COPY . .

# Сборка приложения для продакшена
RUN npm run build

# Производственная стадия с Nginx
FROM nginx:alpine AS production-stage

# Удаление стандартной конфигурации nginx
RUN rm /etc/nginx/conf.d/default.conf

# Копирование кастомной конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копирование собранного приложения
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Экспонирование порта
EXPOSE 8501

# Команда запуска
CMD ["nginx", "-g", "daemon off;"] 