
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

-- Создание перечислений (ENUM)
CREATE TYPE process_type AS ENUM ('extrusion', 'ringing', 'corrugation_soft', 'corrugation_hard');
CREATE TYPE order_status AS ENUM ('planned', 'in_progress', 'completed', 'cancelled');
CREATE TYPE product_type AS ENUM ('shell', 'film', 'label');

-- Таблица материалов
CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50),
    color VARCHAR(50),
    density NUMERIC(10, 3), -- г/см³
    cost_per_kg NUMERIC(10, 2), -- руб/кг
    available_quantity NUMERIC(10, 2), -- кг
    minimum_stock NUMERIC(10, 2), -- кг
    supplier VARCHAR(200)
);

-- Индексы для таблицы материалов
CREATE INDEX idx_materials_name ON materials(name);
CREATE INDEX idx_materials_type ON materials(type);

-- Таблица оборудования
CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    process_type process_type NOT NULL,
    capacity_per_hour NUMERIC(10, 2), -- кг/час
    setup_time_minutes INTEGER, -- минуты
    is_available BOOLEAN DEFAULT TRUE,
    maintenance_schedule TIMESTAMP,
    specifications TEXT -- JSON с техническими характеристиками
);

-- Индексы для таблицы оборудования
CREATE INDEX idx_equipment_process_type ON equipment(process_type);
CREATE INDEX idx_equipment_available ON equipment(is_available);

-- Таблица производственных заказов
CREATE TABLE production_orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    product_type product_type NOT NULL,
    process_type process_type NOT NULL,
    
    -- Связи
    material_id INTEGER REFERENCES materials(id),
    equipment_id INTEGER REFERENCES equipment(id),
    
    -- Технические характеристики
    quantity_kg NUMERIC(10, 2) NOT NULL,
    width_mm INTEGER,
    thickness_mm NUMERIC(5, 2),
    color VARCHAR(50),
    caliber VARCHAR(50),
    
    -- Временные рамки
    order_date DATE NOT NULL,
    delivery_date DATE NOT NULL,
    planned_start TIMESTAMP,
    planned_end TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    
    -- Статус и метрики
    status order_status DEFAULT 'planned',
    priority INTEGER DEFAULT 1,
    waste_percentage NUMERIC(5, 2) DEFAULT 0,
    actual_waste_kg NUMERIC(10, 2) DEFAULT 0
);

-- Индексы для таблицы производственных заказов
CREATE INDEX idx_production_orders_order_number ON production_orders(order_number);
CREATE INDEX idx_production_orders_status ON production_orders(status);
CREATE INDEX idx_production_orders_delivery_date ON production_orders(delivery_date);
CREATE INDEX idx_production_orders_material_id ON production_orders(material_id);
CREATE INDEX idx_production_orders_equipment_id ON production_orders(equipment_id);

-- Таблица расписания производства
CREATE TABLE production_schedules (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES production_orders(id),
    equipment_id INTEGER REFERENCES equipment(id),
    
    scheduled_start TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    setup_time_minutes INTEGER,
    processing_time_minutes INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для таблицы расписания
CREATE INDEX idx_production_schedules_order_id ON production_schedules(order_id);
CREATE INDEX idx_production_schedules_equipment_id ON production_schedules(equipment_id);
CREATE INDEX idx_production_schedules_scheduled_start ON production_schedules(scheduled_start);

-- Таблица логов отходов
CREATE TABLE waste_logs (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES production_orders(id),
    process_type process_type NOT NULL,
    
    waste_type VARCHAR(100),
    quantity_kg NUMERIC(10, 2) NOT NULL,
    reason TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для таблицы логов отходов
CREATE INDEX idx_waste_logs_order_id ON waste_logs(order_id);
CREATE INDEX idx_waste_logs_process_type ON waste_logs(process_type);
CREATE INDEX idx_waste_logs_recorded_at ON waste_logs(recorded_at);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at в production_schedules
CREATE TRIGGER update_production_schedules_updated_at 
    BEFORE UPDATE ON production_schedules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Комментарии к таблицам
COMMENT ON TABLE materials IS 'Таблица материалов для производства';
COMMENT ON TABLE equipment IS 'Таблица производственного оборудования';
COMMENT ON TABLE production_orders IS 'Таблица производственных заказов';
COMMENT ON TABLE production_schedules IS 'Таблица расписания производства';
COMMENT ON TABLE waste_logs IS 'Таблица логов отходов производства';
 