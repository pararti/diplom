# Makefile для системы планирования производства Атлантис-Пак

.PHONY: help build up down restart logs clean init test dev-frontend

# Показать справку
help:
	@echo "Система планирования производства Атлантис-Пак"
	@echo "================================================"
	@echo ""
	@echo "Доступные команды:"
	@echo "  make build         - Собрать Docker образы"
	@echo "  make up            - Запустить все сервисы"
	@echo "  make down          - Остановить все сервисы"
	@echo "  make restart       - Перезапустить все сервисы"
	@echo "  make logs          - Показать логи всех сервисов"
	@echo "  make init          - Инициализировать базу данных"
	@echo "  make clean         - Очистить все Docker ресурсы"
	@echo "  make test          - Запустить тесты"
	@echo "  make dev-frontend  - Запустить фронтенд в режиме разработки"
	@echo "  make install-frontend - Установить зависимости фронтенда"
	@echo ""
	@echo "Доступ к сервисам:"
	@echo "  Веб-интерфейс: http://localhost:8501"
	@echo "  API документация: http://localhost:8000/docs"
	@echo "  PostgreSQL: localhost:5432"

# Собрать образы
build:
	@echo "🏗️  Сборка Docker образов..."
	docker-compose build

# Запустить все сервисы
up:
	@echo "🚀 Запуск всех сервисов..."
	mkdir -p data/import data/export logs
	docker-compose up --build -d
	@echo "✅ Сервисы запущены:"
	@echo "   - Веб-интерфейс (Vue.js): http://localhost:8501"
	@echo "   - API: http://localhost:8000"
	@echo "   - API документация: http://localhost:8000/docs"

# Запустить в foreground
up-fg:
	@echo "🚀 Запуск всех сервисов (foreground)..."
	mkdir -p data/import data/export logs
	docker-compose up --build

# Остановить все сервисы
down:
	@echo "⏹️  Остановка всех сервисов..."
	docker-compose down

# Остановить с удалением томов
down-clean:
	@echo "🧹 Остановка с очисткой данных..."
	docker-compose down -v

# Перезапустить все сервисы
restart:
	@echo "🔄 Перезапуск всех сервисов..."
	docker-compose restart

# Показать логи
logs:
	docker-compose logs --tail=100 -f

# Логи конкретного сервиса
logs-api:
	docker-compose logs --tail=100 -f api

logs-web:
	docker-compose logs --tail=100 -f web

logs-db:
	docker-compose logs --tail=100 -f database

# Инициализация базы данных
init:
	@echo "🗄️  Инициализация базы данных..."
	docker-compose up -d database
	@echo "⏳ Ожидание готовности базы данных..."
	sleep 10
	docker-compose run --rm data_initializer
	@echo "✅ База данных инициализирована"

# Статус сервисов
status:
	@echo "📊 Статус сервисов:"
	docker-compose ps

# Подключение к контейнерам
shell-api:
	docker-compose exec api bash

shell-db:
	docker-compose exec database psql -U atlantis_user atlantis_pack_optimization

shell-web:
	docker-compose exec web sh

# Создание бэкапа базы данных
backup:
	@echo "💾 Создание бэкапа базы данных..."
	mkdir -p backups
	docker-compose exec database pg_dump -U atlantis_user atlantis_pack_optimization > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Бэкап создан в папке backups/"

# Восстановление из бэкапа (использование: make restore BACKUP=backups/backup_20241201_120000.sql)
restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "❌ Укажите файл бэкапа: make restore BACKUP=path/to/backup.sql"; \
		exit 1; \
	fi
	@echo "📥 Восстановление из бэкапа $(BACKUP)..."
	docker-compose exec -T database psql -U atlantis_user atlantis_pack_optimization < $(BACKUP)
	@echo "✅ Бэкап восстановлен"

# Очистка всех Docker ресурсов
clean:
	@echo "🧹 Очистка Docker ресурсов..."
	docker-compose down -v --rmi local --remove-orphans
	docker system prune -f
	@echo "✅ Очистка завершена"

# Полная очистка (включая образы)
clean-all:
	@echo "🧹 Полная очистка Docker..."
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -a -f
	@echo "✅ Полная очистка завершена"

# Тестирование
test:
	@echo "🧪 Запуск тестов..."
	docker-compose run --rm api python -m pytest tests/ -v

# Мониторинг ресурсов
monitor:
	@echo "📊 Мониторинг использования ресурсов:"
	docker stats --no-stream

# Проверка здоровья сервисов
health:
	@echo "🏥 Проверка здоровья сервисов:"
	@echo "API сервер:"
	@curl -s http://localhost:8000/health || echo "❌ API недоступен"
	@echo ""
	@echo "Веб-интерфейс:"
	@curl -s http://localhost:8501 || echo "❌ Веб-интерфейс недоступен"

# Установка зависимостей фронтенда
install-frontend:
	@echo "📦 Установка зависимостей фронтенда..."
	cd frontend && npm install
	@echo "✅ Зависимости фронтенда установлены"

# Запуск фронтенда в режиме разработки
dev-frontend:
	@echo "🖥️  Запуск фронтенда в режиме разработки..."
	@echo "Убедитесь, что API сервер запущен (make up api или запустите API отдельно)"
	cd frontend && npm run dev

# Сборка фронтенда
build-frontend:
	@echo "🏗️  Сборка фронтенда..."
	cd frontend && npm run build
	@echo "✅ Фронтенд собран"

# Установка в режиме разработки (без контейнеров)
dev-setup:
	@echo "🛠️  Настройка среды разработки..."
	python -m venv venv
	@echo "Активируйте виртуальное окружение:"
	@echo "  source venv/bin/activate  # Linux/Mac"
	@echo "  venv\\Scripts\\activate     # Windows"
	@echo "Затем запустите:"
	@echo "  pip install -r requirements.txt"
	@echo "  python main.py full"
	@echo ""
	@echo "Для фронтенда:"
	@echo "  make install-frontend"
	@echo "  make dev-frontend"

# Быстрый перезапуск для разработки
dev-restart:
	docker-compose restart api web

# Просмотр сетей Docker
networks:
	@echo "🌐 Docker сети:"
	docker network ls
	@echo ""
	@echo "Детали сети atlantis_network:"
	docker network inspect code2_atlantis_network || echo "Сеть не найдена"

# По умолчанию показываем справку
.DEFAULT_GOAL := help 