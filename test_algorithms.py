#!/usr/bin/env python3
"""
Тестирование исправленных алгоритмов оптимизации
"""

import sys
import os
sys.path.append('.')

from src.optimization.algorithms_fixed import *
from src.models.production import *
from datetime import datetime, timedelta
from decimal import Decimal
import traceback

def create_test_data():
    """Создание тестовых данных"""
    
    # Тестовое оборудование
    equipment = [
        Equipment(
            id=1, name='Экструдер-1', process_type=ProcessType.EXTRUSION,
            capacity_per_hour=Decimal('100'), setup_time_minutes=30, is_available=True
        ),
        Equipment(
            id=2, name='Кольцеватель-1', process_type=ProcessType.RINGING,
            capacity_per_hour=Decimal('80'), setup_time_minutes=20, is_available=True
        ),
        Equipment(
            id=3, name='Гофратор-1', process_type=ProcessType.CORRUGATION_SOFT,
            capacity_per_hour=Decimal('60'), setup_time_minutes=40, is_available=True
        )
    ]

    # Тестовые заказы
    orders = [
        ProductionOrder(
            id=1, order_number='ORD-001', product_type=ProductType.SHELL,
            process_type=ProcessType.EXTRUSION, material_id=1, quantity_kg=Decimal('500'),
            color='красный', order_date=datetime.now().date(),
            delivery_date=(datetime.now() + timedelta(days=7)).date(), priority=1
        ),
        ProductionOrder(
            id=2, order_number='ORD-002', product_type=ProductType.FILM,
            process_type=ProcessType.EXTRUSION, material_id=1, quantity_kg=Decimal('300'),
            color='синий', order_date=datetime.now().date(),
            delivery_date=(datetime.now() + timedelta(days=5)).date(), priority=2
        ),
        ProductionOrder(
            id=3, order_number='ORD-003', product_type=ProductType.SHELL,
            process_type=ProcessType.RINGING, material_id=2, quantity_kg=Decimal('200'),
            caliber='D100', order_date=datetime.now().date(),
            delivery_date=(datetime.now() + timedelta(days=10)).date(), priority=1
        ),
        ProductionOrder(
            id=4, order_number='ORD-004', product_type=ProductType.FILM,
            process_type=ProcessType.CORRUGATION_SOFT, material_id=3, quantity_kg=Decimal('400'),
            thickness_mm=Decimal('2.5'), order_date=datetime.now().date(),
            delivery_date=(datetime.now() + timedelta(days=8)).date(), priority=3
        )
    ]

    return orders, equipment

def test_waste_calculator():
    """Тестирование калькулятора отходов"""
    print("\n=== Тестирование WasteCalculator ===")
    
    orders, equipment = create_test_data()
    
    # Тест расчета отходов при переходе
    order1 = orders[0]  # Экструзия, красный
    order2 = orders[1]  # Экструзия, синий
    
    waste_factor = WasteCalculator.calculate_transition_waste(order1, order2)
    print(f"Отходы при переходе {order1.color} -> {order2.color}: {waste_factor:.3f}")
    
    # Тест расчета времени переналадки
    setup_time = WasteCalculator.calculate_setup_time(order2, equipment[0], order1)
    print(f"Время переналадки: {setup_time} минут")
    
    # Проверяем корректность значений
    assert 0.04 <= waste_factor <= 0.06, f"Неожиданный коэффициент отходов: {waste_factor}"
    assert 30 <= setup_time <= 60, f"Неожиданное время переналадки: {setup_time}"
    
    return True

def test_genetic_algorithm():
    """Тестирование генетического алгоритма"""
    print("\n=== Тестирование GeneticAlgorithmOptimizer ===")
    
    orders, equipment = create_test_data()
    
    # Создаем задачу оптимизации
    task = OptimizationTask(
        orders=orders,
        equipment=equipment,
        start_time=datetime.now(),
        planning_horizon_hours=168  # 7 дней
    )
    
    # Создаем оптимизатор с малыми параметрами для быстрого тестирования
    optimizer = GeneticAlgorithmOptimizer(
        population_size=20,
        generations=10,
        mutation_rate=0.1,
        crossover_rate=0.8
    )
    
    try:
        result = optimizer.optimize(task)
        
        print(f"Расписание создано: {len(result.schedule)} элементов")
        print(f"Общие отходы: {result.total_waste_kg} кг")
        print(f"Общее время обработки: {result.total_processing_time_hours} часов")
        print(f"Время оптимизации: {result.optimization_time_seconds:.2f} сек")
        print(f"Makespan: {result.makespan_hours:.2f} часов")
        
        # Проверяем корректность расписания
        for item in result.schedule:
            print(f"  Заказ {item.order_id} -> Оборудование {item.equipment_id}: "
                  f"{item.scheduled_start.strftime('%H:%M')} - {item.scheduled_end.strftime('%H:%M')}")
        
        # Базовые проверки
        assert len(result.schedule) == len(orders), "Не все заказы запланированы"
        assert result.total_waste_kg >= 0, "Отрицательные отходы"
        assert result.optimization_time_seconds > 0, "Нулевое время оптимизации"
        
        return True
        
    except Exception as e:
        print(f"Ошибка в генетическом алгоритме: {e}")
        traceback.print_exc()
        return False

def test_branch_and_bound():
    """Тестирование алгоритма ветвей и границ"""
    print("\n=== Тестирование BranchAndBoundOptimizer ===")
    
    orders, equipment = create_test_data()
    
    # Используем только первые 2 заказа для быстрого тестирования
    small_orders = orders[:2]
    
    task = OptimizationTask(
        orders=small_orders,
        equipment=equipment,
        start_time=datetime.now(),
        planning_horizon_hours=168
    )
    
    optimizer = BranchAndBoundOptimizer(max_nodes=1000)
    
    try:
        result = optimizer.optimize(task)
        
        print(f"Расписание создано: {len(result.schedule)} элементов")
        print(f"Общие отходы: {result.total_waste_kg} кг")
        print(f"Время оптимизации: {result.optimization_time_seconds:.2f} сек")
        print(f"Узлов исследовано: {optimizer.nodes_explored}")
        
        # Базовые проверки
        assert len(result.schedule) == len(small_orders), "Не все заказы запланированы"
        assert result.total_waste_kg >= 0, "Отрицательные отходы"
        
        return True
        
    except Exception as e:
        print(f"Ошибка в алгоритме ветвей и границ: {e}")
        traceback.print_exc()
        return False

def test_hybrid_optimizer():
    """Тестирование гибридного оптимизатора"""
    print("\n=== Тестирование HybridOptimizer ===")
    
    orders, equipment = create_test_data()
    
    task = OptimizationTask(
        orders=orders,
        equipment=equipment,
        start_time=datetime.now(),
        planning_horizon_hours=168
    )
    
    optimizer = HybridOptimizer(
        ga_params={'population_size': 20, 'generations': 10},
        bb_max_nodes=1000
    )
    
    try:
        result = optimizer.optimize(task)
        
        print(f"Расписание создано: {len(result.schedule)} элементов")
        print(f"Общие отходы: {result.total_waste_kg} кг")
        print(f"Время оптимизации: {result.optimization_time_seconds:.2f} сек")
        
        # Базовые проверки
        assert len(result.schedule) == len(orders), "Не все заказы запланированы"
        assert result.total_waste_kg >= 0, "Отрицательные отходы"
        
        return True
        
    except Exception as e:
        print(f"Ошибка в гибридном оптимизаторе: {e}")
        traceback.print_exc()
        return False

def test_schedule_validation():
    """Тестирование валидации расписания"""
    print("\n=== Тестирование валидации расписания ===")
    
    orders, equipment = create_test_data()
    
    task = OptimizationTask(
        orders=orders,
        equipment=equipment,
        start_time=datetime.now(),
        planning_horizon_hours=168
    )
    
    optimizer = GeneticAlgorithmOptimizer(population_size=10, generations=5)
    result = optimizer.optimize(task)
    
    # Проверки корректности
    issues = []
    
    # 1. Все заказы должны быть запланированы
    scheduled_orders = {item.order_id for item in result.schedule}
    all_orders = {order.id for order in orders}
    
    if scheduled_orders != all_orders:
        issues.append(f"Не все заказы запланированы: {all_orders - scheduled_orders}")
    
    # 2. Проверка пересечений по времени на одном оборудовании
    equipment_schedules = {}
    for item in result.schedule:
        if item.equipment_id not in equipment_schedules:
            equipment_schedules[item.equipment_id] = []
        equipment_schedules[item.equipment_id].append(item)
    
    for eq_id, schedule in equipment_schedules.items():
        schedule.sort(key=lambda x: x.scheduled_start)
        for i in range(len(schedule) - 1):
            if schedule[i].scheduled_end > schedule[i + 1].scheduled_start:
                issues.append(f"Пересечение времени на оборудовании {eq_id}")
    
    # 3. Проверка соответствия типов процессов
    for item in result.schedule:
        order = next(o for o in orders if o.id == item.order_id)
        eq = next(e for e in equipment if e.id == item.equipment_id)
        
        if order.process_type != eq.process_type:
            issues.append(f"Несоответствие типа процесса: заказ {order.id} ({order.process_type}) -> оборудование {eq.id} ({eq.process_type})")
    
    # 4. Проверка положительности времен
    for item in result.schedule:
        if item.scheduled_start >= item.scheduled_end:
            issues.append(f"Некорректное время для заказа {item.order_id}")
        
        if item.setup_time_minutes < 0 or item.processing_time_minutes <= 0:
            issues.append(f"Некорректные времена переналадки/обработки для заказа {item.order_id}")
    
    if issues:
        print("Найдены проблемы в расписании:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("Расписание корректно!")
        return True

def test_performance():
    """Тестирование производительности"""
    print("\n=== Тестирование производительности ===")
    
    orders, equipment = create_test_data()
    
    # Создаем большую задачу
    large_orders = []
    for i in range(20):  # 20 заказов
        order = ProductionOrder(
            id=i+10, order_number=f'ORD-{i+10:03d}', product_type=ProductType.SHELL,
            process_type=ProcessType.EXTRUSION, material_id=(i % 3) + 1, 
            quantity_kg=Decimal(str(100 + i * 10)),
            color=['красный', 'синий', 'зеленый'][i % 3], 
            order_date=datetime.now().date(),
            delivery_date=(datetime.now() + timedelta(days=i+1)).date(), 
            priority=(i % 3) + 1
        )
        large_orders.append(order)
    
    task = OptimizationTask(
        orders=large_orders,
        equipment=equipment,
        start_time=datetime.now(),
        planning_horizon_hours=168
    )
    
    try:
        # Тестируем генетический алгоритм
        ga_optimizer = GeneticAlgorithmOptimizer(population_size=30, generations=20)
        start_time = time.time()
        ga_result = ga_optimizer.optimize(task)
        ga_time = time.time() - start_time
        
        print(f"Генетический алгоритм:")
        print(f"  Время: {ga_time:.2f} сек")
        print(f"  Отходы: {ga_result.total_waste_kg} кг")
        print(f"  Заказов обработано: {len(ga_result.schedule)}")
        
        # Тестируем гибридный оптимизатор
        hybrid_optimizer = HybridOptimizer(
            ga_params={'population_size': 30, 'generations': 20}
        )
        start_time = time.time()
        hybrid_result = hybrid_optimizer.optimize(task)
        hybrid_time = time.time() - start_time
        
        print(f"Гибридный оптимизатор:")
        print(f"  Время: {hybrid_time:.2f} сек")
        print(f"  Отходы: {hybrid_result.total_waste_kg} кг")
        print(f"  Заказов обработано: {len(hybrid_result.schedule)}")
        
        # Проверки производительности
        assert ga_time < 60, f"Генетический алгоритм слишком медленный: {ga_time} сек"
        assert hybrid_time < 60, f"Гибридный оптимизатор слишком медленный: {hybrid_time} сек"
        assert len(ga_result.schedule) == len(large_orders), "ГА: не все заказы обработаны"
        assert len(hybrid_result.schedule) == len(large_orders), "Гибрид: не все заказы обработаны"
        
        return True
        
    except Exception as e:
        print(f"Ошибка в тестировании производительности: {e}")
        traceback.print_exc()
        return False

def main():
    """Основная функция тестирования"""
    print("=== ТЕСТИРОВАНИЕ ИСПРАВЛЕННЫХ АЛГОРИТМОВ ОПТИМИЗАЦИИ ===")
    
    tests = [
        ("Калькулятор отходов", test_waste_calculator),
        ("Генетический алгоритм", test_genetic_algorithm),
        ("Алгоритм ветвей и границ", test_branch_and_bound),
        ("Гибридный оптимизатор", test_hybrid_optimizer),
        ("Валидация расписания", test_schedule_validation),
        ("Производительность", test_performance),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            print(f"Запуск теста: {test_name}")
            print('='*50)
            
            success = test_func()
            results[test_name] = success
            
            if success:
                print(f"✅ {test_name}: ПРОЙДЕН")
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
                
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")
            traceback.print_exc()
            results[test_name] = False
    
    # Итоговый отчет
    print(f"\n{'='*50}")
    print("ИТОГОВЫЙ ОТЧЕТ")
    print('='*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✨ Алгоритмы оптимизации работают корректно!")
        return 0
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        return 1

if __name__ == "__main__":
    exit(main()) 