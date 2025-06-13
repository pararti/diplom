import random
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session

from src.models.production import (
    Material, Equipment, ProductionOrder, WasteLog,
    ProcessType, ProductType, OrderStatus
)


class SyntheticDataGenerator:
    """Генератор синтетических данных для имитации реального производства"""
    
    def __init__(self):
        self.material_types = [
            "LDPE", "HDPE", "PP", "PVC", "PA", "EVOH"
        ]
        self.colors = [
            "прозрачный", "белый", "красный", "синий", "зеленый", 
            "желтый", "черный", "серый"
        ]
        self.suppliers = [
            "СИБУР", "НИПОМ", "ЛукойлПетрохим", 
            "Полимерсинтез", "Уралхимпласт"
        ]
        self.equipment_names = {
            ProcessType.EXTRUSION: [
                "Экструдер Л65-25", "Экструдер Л90-32", "Экструдер П110-28",
                "Линия экструзии PE-1200", "Экструдер многослойный ML-850"
            ],
            ProcessType.RINGING: [
                "Кольцевальная машина КМ-500", "Линия кольцевания ЛК-800",
                "Автомат кольцевания АК-300", "Станок кольцевой СК-600"
            ],
            ProcessType.CORRUGATION_SOFT: [
                "Гофроустановка ГУ-1000", "Линия гофрирования мягкая ЛГМ-800",
                "Гофроагрегат ГА-600"
            ],
            ProcessType.CORRUGATION_HARD: [
                "Линия гофрирования жесткая ЛГЖ-1200", "Гофроустановка ГУЖ-900",
                "Автомат гофрирования жесткий АГЖ-700"
            ]
        }
    
    def generate_materials(self, db: Session, count: int = 20) -> List[Material]:
        """Генерация материалов"""
        materials = []
        
        for i in range(count):
            material_type = random.choice(self.material_types)
            color = random.choice(self.colors) if random.random() > 0.3 else None
            
            material = Material(
                name=f"{material_type}{'_' + color if color else ''}_{i+1:03d}",
                type=material_type,
                color=color,
                density=Decimal(str(round(random.uniform(0.85, 1.45), 3))),
                cost_per_kg=Decimal(str(round(random.uniform(45, 180), 2))),
                available_quantity=Decimal(str(round(random.uniform(500, 5000), 2))),
                minimum_stock=Decimal(str(round(random.uniform(100, 500), 2))),
                supplier=random.choice(self.suppliers)
            )
            
            db.add(material)
            materials.append(material)
        
        db.commit()
        return materials
    
    def generate_equipment(self, db: Session) -> List[Equipment]:
        """Генерация оборудования"""
        equipment_list = []
        
        for process_type in ProcessType:
            names = self.equipment_names[process_type]
            
            for name in names:
                if process_type == ProcessType.EXTRUSION:
                    capacity = round(random.uniform(50, 200), 2)
                    setup_time = random.randint(30, 120)
                elif process_type == ProcessType.RINGING:
                    capacity = round(random.uniform(80, 150), 2)
                    setup_time = random.randint(15, 60)
                else:  # Гофрирование
                    capacity = round(random.uniform(60, 120), 2)
                    setup_time = random.randint(20, 90)
                
                equipment = Equipment(
                    name=name,
                    process_type=process_type,
                    capacity_per_hour=Decimal(str(capacity)),
                    setup_time_minutes=setup_time,
                    is_available=random.random() > 0.1,  # 90% доступности
                    maintenance_schedule=datetime.now() + timedelta(
                        days=random.randint(1, 90)
                    ) if random.random() > 0.7 else None,
                    specifications='{"max_width": 1200, "max_thickness": 5.0}'
                )
                
                db.add(equipment)
                equipment_list.append(equipment)
        
        db.commit()
        return equipment_list
    
    def generate_production_orders(
        self, 
        db: Session, 
        materials: List[Material], 
        count: int = 100
    ) -> List[ProductionOrder]:
        """Генерация производственных заказов"""
        orders = []
        base_date = date.today()
        
        for i in range(count):
            product_type = random.choice(list(ProductType))

            if product_type == ProductType.SHELL:
                process_type = random.choice([
                    ProcessType.EXTRUSION, ProcessType.RINGING, 
                    ProcessType.CORRUGATION_SOFT, ProcessType.CORRUGATION_HARD
                ])
            elif product_type == ProductType.FILM:
                process_type = random.choice([
                    ProcessType.EXTRUSION, ProcessType.CORRUGATION_SOFT
                ])
            else:
                process_type = ProcessType.EXTRUSION
            
            material = random.choice(materials)
            
            # Генерация характеристик заказа
            order_date = base_date - timedelta(days=random.randint(0, 30))
            delivery_date = order_date + timedelta(days=random.randint(3, 21))
            
            order = ProductionOrder(
                order_number=f"ORD-{datetime.now().year}-{i+1:05d}",
                product_type=product_type,
                process_type=process_type,
                material_id=material.id,
                quantity_kg=Decimal(str(round(random.uniform(50, 2000), 2))),
                width_mm=random.randint(200, 1200) if random.random() > 0.3 else None,
                thickness_mm=Decimal(str(round(random.uniform(0.05, 3.0), 2))) if random.random() > 0.3 else None,
                color=random.choice(self.colors) if random.random() > 0.4 else None,
                caliber=f"D{random.randint(50, 500)}" if process_type == ProcessType.RINGING else None,
                order_date=order_date,
                delivery_date=delivery_date,
                priority=random.randint(1, 5),
                status=random.choice([OrderStatus.PLANNED, OrderStatus.IN_PROGRESS]) 
                    if random.random() > 0.8 else OrderStatus.PLANNED
            )
            
            db.add(order)
            orders.append(order)
        
        db.commit()
        return orders
    
    def generate_waste_logs(
        self, 
        db: Session, 
        orders: List[ProductionOrder], 
        count: int = 50
    ) -> List[WasteLog]:
        """Генерация логов отходов"""
        waste_types = [
            "переналадка", "брак_качества", "обрезки", "пуск_оборудования",
            "остановка_линии", "смена_материала", "регулировка_параметров"
        ]
        
        waste_logs = []
        
        for _ in range(count):
            order = random.choice(orders)

            if order.process_type == ProcessType.EXTRUSION:
                waste_kg = round(random.uniform(1, 50), 2)
            elif order.process_type == ProcessType.RINGING:
                waste_kg = round(random.uniform(0.5, 30), 2)
            else:  # Гофрирование
                waste_kg = round(random.uniform(2, 40), 2)
            
            waste_log = WasteLog(
                order_id=order.id,
                process_type=order.process_type,
                waste_type=random.choice(waste_types),
                quantity_kg=Decimal(str(waste_kg)),
                reason=f"Причина отходов: {random.choice(waste_types)}",
                recorded_at=datetime.now() - timedelta(
                    hours=random.randint(1, 720)
                )
            )
            
            db.add(waste_log)
            waste_logs.append(waste_log)
        
        db.commit()
        return waste_logs
    
    def generate_all_data(self, db: Session) -> dict:
        """Генерация всех синтетических данных"""
        print("Генерация материалов...")
        materials = self.generate_materials(db, count=25)
        
        print("Генерация оборудования...")
        equipment = self.generate_equipment(db)
        
        print("Генерация производственных заказов...")
        orders = self.generate_production_orders(db, materials, count=150)
        
        print("Генерация логов отходов...")
        waste_logs = self.generate_waste_logs(db, orders, count=75)
        
        return {
            "materials": len(materials),
            "equipment": len(equipment),
            "orders": len(orders),
            "waste_logs": len(waste_logs)
        }


def populate_database():
    """Заполнение базы данных синтетическими данными"""
    from src.database.connection import SessionLocal, init_database

    init_database()
    
    db = SessionLocal()
    try:
        generator = SyntheticDataGenerator()
        result = generator.generate_all_data(db)
        
        print(f"Данные успешно сгенерированы:")
        for key, value in result.items():
            print(f"  {key}: {value}")
            
    finally:
        db.close()


if __name__ == "__main__":
    populate_database() 