from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from src.database.connection import get_db
from src.models.production import (
    Material, Equipment, ProductionOrder, ProductionSchedule, WasteLog,
    MaterialCreate, MaterialResponse, MaterialUpdate,
    EquipmentCreate, EquipmentResponse, EquipmentUpdate,
    ProductionOrderCreate, ProductionOrderResponse, ProductionOrderUpdate,
    ProcessType, OrderStatus, ProductType,
    OptimizationResult
)
from src.optimization.algorithms import (
    HybridOptimizer, OptimizationTask, GeneticAlgorithmOptimizer, BranchAndBoundOptimizer
)


app = FastAPI(
    title="Система планирования производства Атлантис-Пак",
    description="Автоматизация и оптимизация планирования производственных процессов",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Корневой маршрут API"""
    return {
        "message": "Система планирования производства Атлантис-Пак",
        "version": "1.0.0",
        "status": "running"
    }


# ===== МАРШРУТЫ ДЛЯ МАТЕРИАЛОВ =====

@app.get("/materials/", response_model=List[MaterialResponse])
async def get_materials(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    type_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получение списка материалов"""
    query = db.query(Material)
    
    if type_filter:
        query = query.filter(Material.type == type_filter)
    
    materials = query.offset(skip).limit(limit).all()
    return materials


@app.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: int, db: Session = Depends(get_db)):
    """Получение материала по ID"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    return material


@app.post("/materials/", response_model=MaterialResponse)
async def create_material(material: MaterialCreate, db: Session = Depends(get_db)):
    """Создание нового материала"""
    db_material = Material(**material.dict())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


@app.put("/materials/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: int, 
    material_update: MaterialUpdate, 
    db: Session = Depends(get_db)
):
    """Обновление материала"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    update_data = material_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(material, field, value)
    
    db.commit()
    db.refresh(material)
    return material


@app.delete("/materials/{material_id}")
async def delete_material(material_id: int, db: Session = Depends(get_db)):
    """Удаление материала"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")

    orders_count = db.query(ProductionOrder).filter(ProductionOrder.material_id == material_id).count()
    if orders_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Невозможно удалить материал. Он используется в {orders_count} заказах"
        )
    
    db.delete(material)
    db.commit()
    return {"message": "Материал успешно удален"}


@app.post("/materials/bulk-import")
async def bulk_import_materials(
    materials_data: List[MaterialCreate],
    db: Session = Depends(get_db)
):
    """Массовый импорт материалов"""
    created_materials = []
    errors = []
    
    for i, material_data in enumerate(materials_data):
        try:
            existing_material = db.query(Material).filter(
                Material.name == material_data.name
            ).first()
            if existing_material:
                errors.append(f"Строка {i+1}: Материал с названием '{material_data.name}' уже существует")
                continue
            
            db_material = Material(**material_data.dict())
            db.add(db_material)
            db.flush()
            created_materials.append(db_material.id)
            
        except Exception as e:
            errors.append(f"Строка {i+1}: {str(e)}")
    
    if created_materials:
        db.commit()
    else:
        db.rollback()
    
    return {
        "created_count": len(created_materials),
        "error_count": len(errors),
        "created_material_ids": created_materials,
        "errors": errors
    }


@app.get("/materials/types/")
async def get_material_types(db: Session = Depends(get_db)):
    """Получение списка уникальных типов материалов"""
    result = db.query(Material.type).distinct().filter(Material.type.isnot(None)).all()
    types = [row[0] for row in result if row[0]]  # Извлекаем строки из кортежей
    return sorted(types)  # Возвращаем отсортированный список


# ===== МАРШРУТЫ ДЛЯ ОБОРУДОВАНИЯ =====

@app.get("/equipment/", response_model=List[EquipmentResponse])
async def get_equipment(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    process_type: Optional[ProcessType] = None,
    available_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Получение списка оборудования"""
    query = db.query(Equipment)
    
    if process_type:
        query = query.filter(Equipment.process_type == process_type)
    
    if available_only:
        query = query.filter(Equipment.is_available == True)
    
    equipment = query.offset(skip).limit(limit).all()
    return equipment


@app.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment_item(equipment_id: int, db: Session = Depends(get_db)):
    """Получение оборудования по ID"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Оборудование не найдено")
    return equipment


@app.post("/equipment/", response_model=EquipmentResponse)
async def create_equipment(equipment: EquipmentCreate, db: Session = Depends(get_db)):
    """Создание нового оборудования"""
    db_equipment = Equipment(**equipment.dict())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


@app.put("/equipment/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: int, 
    equipment_update: EquipmentUpdate, 
    db: Session = Depends(get_db)
):
    """Обновление оборудования"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Оборудование не найдено")
    
    update_data = equipment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(equipment, field, value)
    
    db.commit()
    db.refresh(equipment)
    return equipment


@app.delete("/equipment/{equipment_id}")
async def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    """Удаление оборудования"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Оборудование не найдено")
    
    # Проверяем, используется ли оборудование в расписании
    schedule_count = db.query(ProductionSchedule).filter(ProductionSchedule.equipment_id == equipment_id).count()
    if schedule_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Невозможно удалить оборудование. Оно используется в {schedule_count} записях расписания"
        )
    
    db.delete(equipment)
    db.commit()
    return {"message": "Оборудование успешно удалено"}


@app.post("/equipment/bulk-import")
async def bulk_import_equipment(
    equipment_data: List[EquipmentCreate],
    db: Session = Depends(get_db)
):
    """Массовый импорт оборудования"""
    created_equipment = []
    errors = []
    
    for i, eq_data in enumerate(equipment_data):
        try:
            existing_equipment = db.query(Equipment).filter(
                Equipment.name == eq_data.name
            ).first()
            if existing_equipment:
                errors.append(f"Строка {i+1}: Оборудование с названием '{eq_data.name}' уже существует")
                continue
            
            db_equipment = Equipment(**eq_data.dict())
            db.add(db_equipment)
            db.flush()
            created_equipment.append(db_equipment.id)
            
        except Exception as e:
            errors.append(f"Строка {i+1}: {str(e)}")
    
    if created_equipment:
        db.commit()
    else:
        db.rollback()
    
    return {
        "created_count": len(created_equipment),
        "error_count": len(errors),
        "created_equipment_ids": created_equipment,
        "errors": errors
    }


# ===== МАРШРУТЫ ДЛЯ ПРОИЗВОДСТВЕННЫХ ЗАКАЗОВ =====

@app.get("/orders/", response_model=List[ProductionOrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[OrderStatus] = None,
    process_type: Optional[ProcessType] = None,
    product_type: Optional[ProductType] = None,
    db: Session = Depends(get_db)
):
    """Получение списка производственных заказов"""
    query = db.query(ProductionOrder)
    
    if status:
        query = query.filter(ProductionOrder.status == status)
    
    if process_type:
        query = query.filter(ProductionOrder.process_type == process_type)
    
    if product_type:
        query = query.filter(ProductionOrder.product_type == product_type)
    
    orders = query.offset(skip).limit(limit).all()
    return orders


@app.get("/orders/search", response_model=List[ProductionOrderResponse])
async def search_orders(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    db: Session = Depends(get_db)
):
    """Поиск заказов по номеру заказа"""
    orders = db.query(ProductionOrder).filter(
        ProductionOrder.order_number.ilike(f"%{q}%")
    ).limit(50).all()
    return orders


@app.get("/orders/{order_id}", response_model=ProductionOrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Получение заказа по ID"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


@app.post("/orders/", response_model=ProductionOrderResponse)
async def create_order(order: ProductionOrderCreate, db: Session = Depends(get_db)):
    """Создание нового заказа"""
    material = db.query(Material).filter(Material.id == order.material_id).first()
    if not material:
        raise HTTPException(status_code=400, detail="Материал не найден")
    
    db_order = ProductionOrder(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@app.put("/orders/{order_id}", response_model=ProductionOrderResponse)
async def update_order(
    order_id: int, 
    order_update: ProductionOrderUpdate, 
    db: Session = Depends(get_db)
):
    """Обновление заказа"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    update_data = order_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.commit()
    db.refresh(order)
    return order


@app.delete("/orders/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Удаление заказа"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if order.status == OrderStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400, 
            detail="Нельзя удалить заказ, который находится в процессе выполнения"
        )

    db.query(ProductionSchedule).filter(ProductionSchedule.order_id == order_id).delete()

    db.delete(order)
    db.commit()
    
    return {"message": f"Заказ {order.order_number} успешно удален"}


@app.post("/orders/bulk-import")
async def bulk_import_orders(
    orders_data: List[ProductionOrderCreate],
    db: Session = Depends(get_db)
):
    """Массовый импорт заказов"""
    created_orders = []
    errors = []
    
    for i, order_data in enumerate(orders_data):
        try:
            material = db.query(Material).filter(Material.id == order_data.material_id).first()
            if not material:
                errors.append(f"Строка {i+1}: Материал с ID {order_data.material_id} не найден")
                continue

            existing_order = db.query(ProductionOrder).filter(
                ProductionOrder.order_number == order_data.order_number
            ).first()
            if existing_order:
                errors.append(f"Строка {i+1}: Заказ с номером {order_data.order_number} уже существует")
                continue
            
            db_order = ProductionOrder(**order_data.dict())
            db.add(db_order)
            db.flush()
            created_orders.append(db_order.id)
            
        except Exception as e:
            errors.append(f"Строка {i+1}: {str(e)}")
    
    if created_orders:
        db.commit()
    else:
        db.rollback()
    
    return {
        "created_count": len(created_orders),
        "error_count": len(errors),
        "created_order_ids": created_orders,
        "errors": errors
    }


# ===== МАРШРУТЫ ДЛЯ ОПТИМИЗАЦИИ =====

@app.post("/optimize/schedule", response_model=OptimizationResult)
async def optimize_schedule(
    algorithm: str = Query("hybrid", regex="^(genetic|branch_bound|hybrid)$"),
    planning_horizon_days: int = Query(30, ge=1, le=90),
    population_size: int = Query(100, ge=20, le=500),
    generations: int = Query(50, ge=10, le=200),
    db: Session = Depends(get_db)
):
    """Оптимизация производственного расписания"""

    orders = db.query(ProductionOrder).filter(
        ProductionOrder.status == OrderStatus.PLANNED
    ).all()
    
    if not orders:
        raise HTTPException(status_code=400, detail="Нет заказов для планирования")
    
    equipment = db.query(Equipment).filter(Equipment.is_available == True).all()
    
    if not equipment:
        raise HTTPException(status_code=400, detail="Нет доступного оборудования")

    task = OptimizationTask(
        orders=orders,
        equipment=equipment,
        start_time=datetime.now(),
        planning_horizon_hours=planning_horizon_days * 24
    )

    if algorithm == "genetic":
        optimizer = GeneticAlgorithmOptimizer(
            population_size=population_size,
            generations=generations
        )
    elif algorithm == "branch_bound":
        optimizer = BranchAndBoundOptimizer(max_nodes=10000)
    else:  # hybrid
        optimizer = HybridOptimizer(
            ga_params={
                'population_size': population_size,
                'generations': generations
            }
        )

    # Запускаем оптимизацию
    try:
        result = optimizer.optimize(task)

        await save_optimization_result(result, db)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка оптимизации: {str(e)}")


async def save_optimization_result(result: OptimizationResult, db: Session):
    """Сохранение результатов оптимизации в базу данных"""
    try:
        db.query(ProductionSchedule).delete()
        
        # Сохраняем новые расписания
        for schedule_item in result.schedule:
            db_schedule = ProductionSchedule(
                order_id=schedule_item.order_id,
                equipment_id=schedule_item.equipment_id,
                scheduled_start=schedule_item.scheduled_start,
                scheduled_end=schedule_item.scheduled_end,
                setup_time_minutes=schedule_item.setup_time_minutes,
                processing_time_minutes=schedule_item.processing_time_minutes
            )
            db.add(db_schedule)

        for schedule_item in result.schedule:
            order = db.query(ProductionOrder).filter(
                ProductionOrder.id == schedule_item.order_id
            ).first()
            
            if order:
                order.equipment_id = schedule_item.equipment_id
                order.planned_start = schedule_item.scheduled_start
                order.planned_end = schedule_item.scheduled_end
                order.status = OrderStatus.PLANNED
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


@app.get("/schedule/", response_model=List[dict])
async def get_current_schedule(
    equipment_id: Optional[int] = None,
    start_date: Optional[str] = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db)
):
    """Получение текущего расписания"""
    query = db.query(ProductionSchedule).join(ProductionOrder).join(Equipment)
    
    if equipment_id:
        query = query.filter(ProductionSchedule.equipment_id == equipment_id)
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(ProductionSchedule.scheduled_start >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(ProductionSchedule.scheduled_end < end_dt)
    
    schedules = query.all()
    
    result = []
    for schedule in schedules:
        order = db.query(ProductionOrder).filter(
            ProductionOrder.id == schedule.order_id
        ).first()
        equipment = db.query(Equipment).filter(
            Equipment.id == schedule.equipment_id
        ).first()
        
        result.append({
            "schedule_id": schedule.id,
            "order_id": schedule.order_id,
            "order_number": order.order_number if order else None,
            "equipment_id": schedule.equipment_id,
            "equipment_name": equipment.name if equipment else None,
            "scheduled_start": schedule.scheduled_start,
            "scheduled_end": schedule.scheduled_end,
            "setup_time_minutes": schedule.setup_time_minutes,
            "processing_time_minutes": schedule.processing_time_minutes,
            "product_type": order.product_type if order else None,
            "process_type": order.process_type if order else None,
            "quantity_kg": order.quantity_kg if order else None
        })
    
    return result


# ===== МАРШРУТЫ ДЛЯ АНАЛИТИКИ =====

@app.get("/analytics/waste-summary")
async def get_waste_summary(
    start_date: Optional[str] = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    process_type: Optional[ProcessType] = None,
    db: Session = Depends(get_db)
):
    """Аналитика по отходам"""
    query = db.query(WasteLog)
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(WasteLog.recorded_at >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(WasteLog.recorded_at < end_dt)
    
    if process_type:
        query = query.filter(WasteLog.process_type == process_type)
    
    waste_logs = query.all()

    total_waste = sum(float(log.quantity_kg) for log in waste_logs)
    waste_by_type = {}
    waste_by_process = {}
    
    for log in waste_logs:
        # По типу отходов
        if log.waste_type not in waste_by_type:
            waste_by_type[log.waste_type] = 0
        waste_by_type[log.waste_type] += float(log.quantity_kg)
        
        # По процессам
        if log.process_type not in waste_by_process:
            waste_by_process[log.process_type] = 0
        waste_by_process[log.process_type] += float(log.quantity_kg)
    
    return {
        "total_waste_kg": total_waste,
        "waste_by_type": waste_by_type,
        "waste_by_process": waste_by_process,
        "total_incidents": len(waste_logs)
    }


@app.get("/analytics/equipment-utilization")
async def get_equipment_utilization(
    start_date: Optional[str] = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db)
):
    """Аналитика загрузки оборудования"""
    query = db.query(ProductionSchedule).join(Equipment)
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(ProductionSchedule.scheduled_start >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(ProductionSchedule.scheduled_end < end_dt)
    
    schedules = query.all()
    equipment_list = db.query(Equipment).all()
    
    # Рассчитываем загрузку
    utilization = {}
    
    for equipment in equipment_list:
        eq_schedules = [s for s in schedules if s.equipment_id == equipment.id]
        
        if eq_schedules:
            total_working_time = sum(
                (s.scheduled_end - s.scheduled_start).total_seconds() / 3600
                for s in eq_schedules
            )

            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                total_hours = (end_dt - start_dt).total_seconds() / 3600
            else:
                total_hours = 24 * 30  # 30 дней по умолчанию
            
            utilization_rate = min(total_working_time / total_hours, 1.0)
        else:
            utilization_rate = 0.0
        
        utilization[equipment.id] = {
            "equipment_name": equipment.name,
            "process_type": equipment.process_type,
            "utilization_rate": round(utilization_rate * 100, 2),
            "total_working_hours": round(total_working_time, 2) if eq_schedules else 0,
            "scheduled_orders": len(eq_schedules)
        }
    
    return utilization


@app.get("/health")
async def health_check():
    """Проверка состояния API"""
    return {"status": "healthy", "timestamp": datetime.now()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 