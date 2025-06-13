-- Инициализация базы данных для системы планирования производства Атлантис-Пак

-- Создание пользователя и базы данных (если еще не созданы)
-- Эти команды выполняются при первом запуске контейнера PostgreSQL

-- Установка временной зоны
SET timezone = 'Europe/Moscow';

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Комментарии к базе данных
COMMENT ON DATABASE atlantis_pack_optimization IS 'База данных системы планирования производства Атлантис-Пак';

-- Настройки производительности для PostgreSQL (только динамические параметры)
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Перезагрузка конфигурации
SELECT pg_reload_conf(); 