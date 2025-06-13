import random
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np
from deap import base, creator, tools, algorithms

from src.models.production import ProductionOrder, Equipment, ProcessType, ScheduleItem


@dataclass
class OptimizationTask:
    """Задача оптимизации планирования"""
    orders: List[ProductionOrder]
    equipment: List[Equipment]
    start_time: datetime
    planning_horizon_hours: int = 720  # 30 дней


@dataclass
class OptimizationResult:
    """Результат оптимизации"""
    schedule: List[ScheduleItem]
    total_waste_kg: Decimal
    total_processing_time_hours: Decimal
    equipment_utilization: Dict[int, float]
    waste_reduction_percentage: float
    makespan_hours: float
    optimization_time_seconds: float


class WasteCalculator:
    """Калькулятор отходов производства"""
    

    TRANSITION_WASTE_FACTORS = {
        (ProcessType.EXTRUSION, ProcessType.EXTRUSION): {
            'same_material_same_color': 0.02,
            'same_material_diff_color': 0.05,
            'diff_material_same_color': 0.08,
            'diff_material_diff_color': 0.12,
        },
        (ProcessType.RINGING, ProcessType.RINGING): {
            'same_caliber': 0.015,
            'diff_caliber_small': 0.03,
            'diff_caliber_large': 0.06,
        },
        (ProcessType.CORRUGATION_SOFT, ProcessType.CORRUGATION_SOFT): {
            'same_thickness': 0.025,
            'diff_thickness_small': 0.04,
            'diff_thickness_large': 0.07,
        },
        (ProcessType.CORRUGATION_HARD, ProcessType.CORRUGATION_HARD): {
            'same_thickness': 0.03,
            'diff_thickness_small': 0.05,
            'diff_thickness_large': 0.08,
        }
    }
    
    @staticmethod
    def calculate_transition_waste(order1: ProductionOrder, order2: ProductionOrder) -> float:
        """Расчет отходов при переходе между заказами"""
        if order1.process_type != order2.process_type:
            return 0.15
        
        process_factors = WasteCalculator.TRANSITION_WASTE_FACTORS.get(
            (order1.process_type, order2.process_type), {}
        )
        
        if order1.process_type == ProcessType.EXTRUSION:
            # Учитываем материал и цвет
            same_material = order1.material_id == order2.material_id
            same_color = order1.color == order2.color
            
            if same_material and same_color:
                return process_factors.get('same_material_same_color', 0.03)
            elif same_material:
                return process_factors.get('same_material_diff_color', 0.05)
            elif same_color:
                return process_factors.get('diff_material_same_color', 0.08)
            else:
                return process_factors.get('diff_material_diff_color', 0.12)
                
        elif order1.process_type == ProcessType.RINGING:
            if order1.caliber == order2.caliber:
                return process_factors.get('same_caliber', 0.015)
            else:
                try:
                    cal1 = int(order1.caliber.replace('D', '')) if order1.caliber else 0
                    cal2 = int(order2.caliber.replace('D', '')) if order2.caliber else 0
                    diff = abs(cal1 - cal2)
                    
                    if diff <= 50:
                        return process_factors.get('diff_caliber_small', 0.03)
                    else:
                        return process_factors.get('diff_caliber_large', 0.06)
                except:
                    return 0.05
                    
        elif order1.process_type in [ProcessType.CORRUGATION_SOFT, ProcessType.CORRUGATION_HARD]:

            if order1.thickness_mm == order2.thickness_mm:
                return process_factors.get('same_thickness', 0.025)
            else:

                if order1.thickness_mm and order2.thickness_mm:
                    diff = abs(float(order1.thickness_mm) - float(order2.thickness_mm))
                    
                    if diff <= 0.5:
                        return process_factors.get('diff_thickness_small', 0.04)
                    else:
                        return process_factors.get('diff_thickness_large', 0.07)
                else:
                    return 0.05
        
        return 0.05
    
    @staticmethod
    def calculate_setup_time(order: ProductionOrder, equipment: Equipment, prev_order: Optional[ProductionOrder] = None) -> int:
        """Расчет времени переналадки в минутах"""
        base_setup_time = equipment.setup_time_minutes or 30
        
        if prev_order is None:
            return base_setup_time

        if order.process_type != prev_order.process_type:
            return base_setup_time * 2

        transition_factor = WasteCalculator.calculate_transition_waste(prev_order, order)
        additional_time = int(base_setup_time * transition_factor)
        
        return base_setup_time + additional_time


class GeneticAlgorithmOptimizer:
    """Генетический алгоритм для оптимизации планирования"""
    
    def __init__(self, population_size=100, generations=50, mutation_rate=0.1, crossover_rate=0.8):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.toolbox = None
    
    def _setup_deap(self):

        if hasattr(creator, "FitnessMin"):
            del creator.FitnessMin
        if hasattr(creator, "Individual"):
            del creator.Individual
            
        creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        
        self.toolbox = base.Toolbox()
    
    def create_individual(self, task: OptimizationTask) -> Any:
        """Создание индивидуума (расписания)"""
        # Индивидуум представляется как список пар (order_id, equipment_id)
        individual = []
        
        for order in task.orders:
            # Выбираем подходящее оборудование для заказа
            suitable_equipment = [
                eq for eq in task.equipment 
                if eq.process_type == order.process_type and eq.is_available
            ]
            
            if suitable_equipment:
                selected_equipment = random.choice(suitable_equipment)
                individual.append((order.id, selected_equipment.id))
            else:
                # Если нет подходящего оборудования, берем первое доступное
                available_equipment = [eq for eq in task.equipment if eq.is_available]
                if available_equipment:
                    individual.append((order.id, available_equipment[0].id))
        
        return creator.Individual(individual)
    
    def evaluate_individual(self, individual: List[Tuple[int, int]], task: OptimizationTask) -> Tuple[float, float]:
        """Оценка качества индивидуума"""
        schedule = self.decode_individual(individual, task)
        
        total_waste = 0.0
        total_time = 0.0
        
        # Группируем по оборудованию
        equipment_schedules = {}
        for item in schedule:
            if item.equipment_id not in equipment_schedules:
                equipment_schedules[item.equipment_id] = []
            equipment_schedules[item.equipment_id].append(item)
        
        # Рассчитываем метрики для каждого оборудования
        for eq_id, eq_schedule in equipment_schedules.items():
            eq_schedule.sort(key=lambda x: x.scheduled_start)
            
            prev_order = None
            for i, item in enumerate(eq_schedule):
                order = next(o for o in task.orders if o.id == item.order_id)
                
                # Рассчитываем отходы
                if prev_order:
                    waste_factor = WasteCalculator.calculate_transition_waste(prev_order, order)
                    waste = float(order.quantity_kg) * waste_factor
                    total_waste += waste
                
                # Рассчитываем общее время
                duration = (item.scheduled_end - item.scheduled_start).total_seconds() / 3600
                total_time += duration
                
                prev_order = order
        
        return total_waste, total_time
    
    def decode_individual(self, individual: List[Tuple[int, int]], task: OptimizationTask) -> List[ScheduleItem]:
        """Декодирование индивидуума в расписание"""
        schedule = []
        equipment_last_time = {}  # Последнее время окончания для каждого оборудования
        
        # Сортируем заказы по приоритету и срокам
        order_equipment_pairs = []
        for order_id, equipment_id in individual:
            order = next(o for o in task.orders if o.id == order_id)
            order_equipment_pairs.append((order, equipment_id))
        
        order_equipment_pairs.sort(key=lambda x: (x[0].priority, x[0].delivery_date))
        
        for order, equipment_id in order_equipment_pairs:
            equipment = next(eq for eq in task.equipment if eq.id == equipment_id)
            
            # Определяем время начала
            last_end_time = equipment_last_time.get(equipment_id, task.start_time)
            
            # Получаем предыдущий заказ на этом оборудовании
            prev_orders = [s for s in schedule if s.equipment_id == equipment_id]
            prev_order = None
            if prev_orders:
                last_item = max(prev_orders, key=lambda x: x.scheduled_end)
                prev_order = next(o for o in task.orders if o.id == last_item.order_id)
            
            # Рассчитываем время переналадки
            setup_time = WasteCalculator.calculate_setup_time(order, equipment, prev_order)
            
            # Рассчитываем время производства
            if equipment.capacity_per_hour and equipment.capacity_per_hour > 0:
                processing_minutes = int((float(order.quantity_kg) / float(equipment.capacity_per_hour)) * 60)
            else:
                processing_minutes = 60  # Базовое время
            
            # Определяем временные рамки
            scheduled_start = last_end_time + timedelta(minutes=setup_time)
            scheduled_end = scheduled_start + timedelta(minutes=processing_minutes)
            
            schedule_item = ScheduleItem(
                order_id=order.id,
                equipment_id=equipment_id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                setup_time_minutes=setup_time,
                processing_time_minutes=processing_minutes
            )
            
            schedule.append(schedule_item)
            equipment_last_time[equipment_id] = scheduled_end
        
        return schedule
    
    def crossover(self, ind1: Any, ind2: Any) -> Tuple[Any, Any]:
        """Операция скрещивания"""
        if len(ind1) != len(ind2):
            return ind1, ind2
        
        # Точка скрещивания
        cx_point = random.randint(1, len(ind1) - 1)
        
        # Создаем потомков
        offspring1 = creator.Individual(ind1[:cx_point] + ind2[cx_point:])
        offspring2 = creator.Individual(ind2[:cx_point] + ind1[cx_point:])
        
        return offspring1, offspring2
    
    def mutate(self, individual: Any, task: OptimizationTask) -> Tuple[Any]:
        """Операция мутации"""
        mutated = creator.Individual(individual[:])
        
        for i in range(len(mutated)):
            if random.random() < self.mutation_rate:
                order_id, _ = mutated[i]
                order = next(o for o in task.orders if o.id == order_id)
                
                # Выбираем новое подходящее оборудование
                suitable_equipment = [
                    eq for eq in task.equipment 
                    if eq.process_type == order.process_type and eq.is_available
                ]
                
                if suitable_equipment:
                    new_equipment = random.choice(suitable_equipment)
                    mutated[i] = (order_id, new_equipment.id)
        
        return mutated,
    
    def optimize(self, task: OptimizationTask) -> OptimizationResult:
        """Основной метод оптимизации"""
        start_time = time.time()
        
        # Настройка DEAP
        self._setup_deap()
        
        # Настройка инструментов DEAP
        self.toolbox.register("individual", self.create_individual, task)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self.evaluate_individual, task=task)
        self.toolbox.register("mate", self.crossover)
        self.toolbox.register("mutate", self.mutate, task=task)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        
        # Создание начальной популяции
        population = self.toolbox.population(n=self.population_size)
        
        # Оценка начальной популяции
        fitnesses = list(map(self.toolbox.evaluate, population))
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
        
        # Статистика
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("min", np.min, axis=0)
        
        # Запуск алгоритма
        population, logbook = algorithms.eaSimple(
            population, self.toolbox,
            cxpb=self.crossover_rate,
            mutpb=self.mutation_rate,
            ngen=self.generations,
            stats=stats,
            verbose=False
        )
        
        # Получение лучшего решения
        best_individual = tools.selBest(population, 1)[0]
        best_schedule = self.decode_individual(best_individual, task)
        
        # Расчет метрик
        total_waste, total_time = self.evaluate_individual(best_individual, task)
        
        # Расчет загрузки оборудования
        equipment_utilization = {}
        equipment_schedules = {}
        
        for item in best_schedule:
            if item.equipment_id not in equipment_schedules:
                equipment_schedules[item.equipment_id] = []
            equipment_schedules[item.equipment_id].append(item)
        
        for eq_id, eq_schedule in equipment_schedules.items():
            if eq_schedule:
                total_working_time = sum(
                    (item.scheduled_end - item.scheduled_start).total_seconds() / 3600
                    for item in eq_schedule
                )
                planning_horizon = task.planning_horizon_hours
                equipment_utilization[eq_id] = min(total_working_time / planning_horizon, 1.0)
            else:
                equipment_utilization[eq_id] = 0.0
        
        # Расчет makespan
        if best_schedule:
            makespan = max(item.scheduled_end for item in best_schedule) - task.start_time
            makespan_hours = makespan.total_seconds() / 3600
        else:
            makespan_hours = 0.0
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            schedule=best_schedule,
            total_waste_kg=Decimal(str(total_waste)),
            total_processing_time_hours=Decimal(str(total_time)),
            equipment_utilization=equipment_utilization,
            waste_reduction_percentage=0.0,  # Будет рассчитано позже
            makespan_hours=makespan_hours,
            optimization_time_seconds=optimization_time
        )


class BranchAndBoundOptimizer:
    """Алгоритм ветвей и границ для точной оптимизации малых задач"""
    
    def __init__(self, max_nodes=10000):
        self.max_nodes = max_nodes
        self.nodes_explored = 0
        self.best_solution = None
        self.best_value = float('inf')
        self.task = None  # Сохраняем ссылку на задачу
    
    def optimize(self, task: OptimizationTask) -> OptimizationResult:
        """Оптимизация методом ветвей и границ"""
        start_time = time.time()
        self.task = task  # Сохраняем задачу для использования в методах
        
        # Для больших задач используем эвристику
        if len(task.orders) > 20:
            return self._heuristic_solve(task, start_time)
        
        # Точное решение для малых задач
        self.nodes_explored = 0
        self.best_solution = None
        self.best_value = float('inf')
        
        # Начальное состояние
        initial_state = {
            'assigned_orders': [],
            'remaining_orders': task.orders.copy(),
            'equipment_schedules': {eq.id: [] for eq in task.equipment if eq.is_available},
            'current_time': {eq.id: task.start_time for eq in task.equipment if eq.is_available}
        }
        
        self._branch_and_bound(initial_state, task)
        
        if self.best_solution:
            return self._create_result(self.best_solution, task, start_time)
        else:
            # Fallback к эвристике
            return self._heuristic_solve(task, start_time)
    
    def _branch_and_bound(self, state: dict, task: OptimizationTask):
        """Рекурсивный метод ветвей и границ"""
        self.nodes_explored += 1
        
        if self.nodes_explored > self.max_nodes:
            return
        
        # Если все заказы назначены
        if not state['remaining_orders']:
            value = self._evaluate_state(state, task)
            if value < self.best_value:
                self.best_value = value
                self.best_solution = state.copy()
            return
        
        # Выбираем следующий заказ (самый срочный)
        next_order = min(state['remaining_orders'], key=lambda o: o.delivery_date)
        
        # Пробуем назначить на каждое подходящее оборудование
        suitable_equipment = [
            eq for eq in task.equipment 
            if eq.process_type == next_order.process_type and eq.is_available
        ]
        
        for equipment in suitable_equipment:
            # Создаем новое состояние
            new_state = self._create_new_state(state, next_order, equipment, task)
            
            # Проверяем границу
            lower_bound = self._calculate_lower_bound(new_state, task)
            if lower_bound < self.best_value:
                self._branch_and_bound(new_state, task)
    
    def _create_new_state(self, state: dict, order: ProductionOrder, equipment: Equipment, task: OptimizationTask) -> dict:
        """Создание нового состояния после назначения заказа"""
        new_state = {
            'assigned_orders': state['assigned_orders'] + [(order.id, equipment.id)],
            'remaining_orders': [o for o in state['remaining_orders'] if o.id != order.id],
            'equipment_schedules': {k: v.copy() for k, v in state['equipment_schedules'].items()},
            'current_time': state['current_time'].copy()
        }
        
        # Обновляем расписание оборудования
        current_time = new_state['current_time'][equipment.id]
        
        # Рассчитываем время переналадки
        prev_order = None
        if new_state['equipment_schedules'][equipment.id]:
            last_order_id = new_state['equipment_schedules'][equipment.id][-1][0]
            prev_order = next(o for o in task.orders if o.id == last_order_id)
        
        setup_time = WasteCalculator.calculate_setup_time(order, equipment, prev_order)
        
        # Рассчитываем время производства
        if equipment.capacity_per_hour and equipment.capacity_per_hour > 0:
            processing_minutes = int((float(order.quantity_kg) / float(equipment.capacity_per_hour)) * 60)
        else:
            processing_minutes = 60
        
        start_time = current_time + timedelta(minutes=setup_time)
        end_time = start_time + timedelta(minutes=processing_minutes)
        
        new_state['equipment_schedules'][equipment.id].append((order.id, start_time, end_time))
        new_state['current_time'][equipment.id] = end_time
        
        return new_state
    
    def _calculate_lower_bound(self, state: dict, task: OptimizationTask) -> float:
        """Расчет нижней границы для отсечения"""
        # Простая нижняя граница - сумма минимальных отходов для оставшихся заказов
        total_waste = 0.0
        
        # Отходы для уже назначенных заказов
        for eq_id, schedule in state['equipment_schedules'].items():
            prev_order = None
            for order_id, start_time, end_time in schedule:
                order = next(o for o in task.orders if o.id == order_id)
                
                if prev_order:
                    waste_factor = WasteCalculator.calculate_transition_waste(prev_order, order)
                    total_waste += float(order.quantity_kg) * waste_factor
                
                prev_order = order
        
        # Минимальные отходы для оставшихся заказов
        for order in state['remaining_orders']:
            total_waste += float(order.quantity_kg) * 0.01  # Минимальный уровень отходов
        
        return total_waste
    
    def _evaluate_state(self, state: dict, task: OptimizationTask) -> float:
        """Оценка полного состояния"""
        total_waste = 0.0
        
        for eq_id, schedule in state['equipment_schedules'].items():
            prev_order = None
            for order_id, start_time, end_time in schedule:
                order = next(o for o in task.orders if o.id == order_id)
                
                if prev_order:
                    waste_factor = WasteCalculator.calculate_transition_waste(prev_order, order)
                    total_waste += float(order.quantity_kg) * waste_factor
                
                prev_order = order
        
        return total_waste
    
    def _heuristic_solve(self, task: OptimizationTask, start_time: float) -> OptimizationResult:
        """Эвристическое решение для больших задач"""
        # Сортируем заказы по приоритету и срокам
        sorted_orders = sorted(task.orders, key=lambda o: (o.priority, o.delivery_date))
        
        schedule = []
        equipment_last_time = {eq.id: task.start_time for eq in task.equipment if eq.is_available}
        
        for order in sorted_orders:
            # Найти подходящее оборудование
            suitable_equipment = [
                eq for eq in task.equipment 
                if eq.process_type == order.process_type and eq.is_available
            ]
            
            if not suitable_equipment:
                continue
            
            # Выбираем оборудование с наименьшим временем окончания
            best_equipment = min(suitable_equipment, key=lambda eq: equipment_last_time[eq.id])
            
            # Получаем предыдущий заказ
            prev_orders = [s for s in schedule if s.equipment_id == best_equipment.id]
            prev_order = None
            if prev_orders:
                last_item = max(prev_orders, key=lambda x: x.scheduled_end)
                prev_order = next(o for o in sorted_orders if o.id == last_item.order_id)
            
            # Рассчитываем времена
            setup_time = WasteCalculator.calculate_setup_time(order, best_equipment, prev_order)
            
            if best_equipment.capacity_per_hour and best_equipment.capacity_per_hour > 0:
                processing_minutes = int((float(order.quantity_kg) / float(best_equipment.capacity_per_hour)) * 60)
            else:
                processing_minutes = 60
            
            scheduled_start = equipment_last_time[best_equipment.id] + timedelta(minutes=setup_time)
            scheduled_end = scheduled_start + timedelta(minutes=processing_minutes)
            
            schedule_item = ScheduleItem(
                order_id=order.id,
                equipment_id=best_equipment.id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                setup_time_minutes=setup_time,
                processing_time_minutes=processing_minutes
            )
            
            schedule.append(schedule_item)
            equipment_last_time[best_equipment.id] = scheduled_end
        
        return self._create_result({'schedule': schedule}, task, start_time)
    
    def _create_result(self, solution: dict, task: OptimizationTask, start_time: float) -> OptimizationResult:
        """Создание результата оптимизации"""
        if 'schedule' in solution:
            schedule = solution['schedule']
        else:
            # Преобразуем из формата состояния
            schedule = []
            for eq_id, eq_schedule in solution['equipment_schedules'].items():
                for order_id, start_time_dt, end_time_dt in eq_schedule:
                    order = next(o for o in task.orders if o.id == order_id)
                    equipment = next(eq for eq in task.equipment if eq.id == eq_id)
                    
                    processing_minutes = int((end_time_dt - start_time_dt).total_seconds() / 60)
                    setup_time = 30  # Базовое время
                    
                    schedule_item = ScheduleItem(
                        order_id=order_id,
                        equipment_id=eq_id,
                        scheduled_start=start_time_dt,
                        scheduled_end=end_time_dt,
                        setup_time_minutes=setup_time,
                        processing_time_minutes=processing_minutes
                    )
                    schedule.append(schedule_item)
        
        # Расчет метрик
        total_waste = 0.0
        total_time = sum((item.scheduled_end - item.scheduled_start).total_seconds() / 3600 for item in schedule)
        
        # Группируем по оборудованию для расчета отходов
        equipment_schedules = {}
        for item in schedule:
            if item.equipment_id not in equipment_schedules:
                equipment_schedules[item.equipment_id] = []
            equipment_schedules[item.equipment_id].append(item)
        
        for eq_id, eq_schedule in equipment_schedules.items():
            eq_schedule.sort(key=lambda x: x.scheduled_start)
            
            prev_order = None
            for item in eq_schedule:
                order = next(o for o in task.orders if o.id == item.order_id)
                
                if prev_order:
                    waste_factor = WasteCalculator.calculate_transition_waste(prev_order, order)
                    total_waste += float(order.quantity_kg) * waste_factor
                
                prev_order = order
        
        # Загрузка оборудования
        equipment_utilization = {}
        for eq in task.equipment:
            if eq.is_available:
                eq_items = [item for item in schedule if item.equipment_id == eq.id]
                if eq_items:
                    working_time = sum(
                        (item.scheduled_end - item.scheduled_start).total_seconds() / 3600
                        for item in eq_items
                    )
                    equipment_utilization[eq.id] = min(working_time / task.planning_horizon_hours, 1.0)
                else:
                    equipment_utilization[eq.id] = 0.0
        
        # Makespan
        if schedule:
            makespan = max(item.scheduled_end for item in schedule) - task.start_time
            makespan_hours = makespan.total_seconds() / 3600
        else:
            makespan_hours = 0.0
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            schedule=schedule,
            total_waste_kg=Decimal(str(total_waste)),
            total_processing_time_hours=Decimal(str(total_time)),
            equipment_utilization=equipment_utilization,
            waste_reduction_percentage=0.0,
            makespan_hours=makespan_hours,
            optimization_time_seconds=optimization_time
        )


class HybridOptimizer:
    """Гибридный оптимизатор, объединяющий генетический алгоритм и метод ветвей и границ"""
    
    def __init__(self, ga_params=None, bb_max_nodes=10000):
        self.ga_params = ga_params or {}
        self.bb_max_nodes = bb_max_nodes
        
        self.ga_optimizer = GeneticAlgorithmOptimizer(**self.ga_params)
        self.bb_optimizer = BranchAndBoundOptimizer(max_nodes=bb_max_nodes)
    
    def optimize(self, task: OptimizationTask) -> OptimizationResult:
        """Гибридная оптимизация"""
        start_time = time.time()
        
        # Для малых задач используем точный алгоритм
        if len(task.orders) <= 15:
            result = self.bb_optimizer.optimize(task)
        else:
            # Для больших задач используем генетический алгоритм
            result = self.ga_optimizer.optimize(task)
        
        # Корректируем время оптимизации
        result.optimization_time_seconds = time.time() - start_time
        
        return result 