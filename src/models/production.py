from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric, Date, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class ProcessType(str, Enum):
    EXTRUSION = "extrusion"
    RINGING = "ringing"
    CORRUGATION_SOFT = "corrugation_soft"
    CORRUGATION_HARD = "corrugation_hard"


class OrderStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProductType(str, Enum):
    SHELL = "shell"
    FILM = "film"
    LABEL = "label"


# SQLAlchemy Models
class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50))
    color = Column(String(50))
    density = Column(Numeric(10, 3))  # г/см³
    cost_per_kg = Column(Numeric(10, 2))  # руб/кг
    available_quantity = Column(Numeric(10, 2))  # кг
    minimum_stock = Column(Numeric(10, 2))  # кг
    supplier = Column(String(200))
    
    production_orders = relationship("ProductionOrder", back_populates="material")


class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    process_type = Column(SQLEnum(ProcessType), nullable=False)
    capacity_per_hour = Column(Numeric(10, 2))  # кг/час
    setup_time_minutes = Column(Integer)  # минуты
    is_available = Column(Boolean, default=True)
    maintenance_schedule = Column(DateTime)
    specifications = Column(Text)  # JSON с техническими характеристиками
    
    production_orders = relationship("ProductionOrder", back_populates="equipment")


class ProductionOrder(Base):
    __tablename__ = "production_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False)
    product_type = Column(SQLEnum(ProductType), nullable=False)
    process_type = Column(SQLEnum(ProcessType), nullable=False)
    
    # Связи
    material_id = Column(Integer, ForeignKey("materials.id"))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    
    # Технические характеристики
    quantity_kg = Column(Numeric(10, 2), nullable=False)
    width_mm = Column(Integer)
    thickness_mm = Column(Numeric(5, 2))
    color = Column(String(50))
    caliber = Column(String(50))
    
    # Временные рамки
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=False)
    planned_start = Column(DateTime)
    planned_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Статус и метрики
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PLANNED)
    priority = Column(Integer, default=1)
    waste_percentage = Column(Numeric(5, 2), default=0)
    actual_waste_kg = Column(Numeric(10, 2), default=0)
    
    # Связи
    material = relationship("Material", back_populates="production_orders")
    equipment = relationship("Equipment", back_populates="production_orders")


class ProductionSchedule(Base):
    __tablename__ = "production_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("production_orders.id"))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    setup_time_minutes = Column(Integer)
    processing_time_minutes = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WasteLog(Base):
    __tablename__ = "waste_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("production_orders.id"))
    process_type = Column(SQLEnum(ProcessType), nullable=False)
    
    waste_type = Column(String(100))
    quantity_kg = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class MaterialBase(BaseModel):
    name: str
    type: str
    color: Optional[str] = None
    density: Optional[Decimal] = None
    cost_per_kg: Optional[Decimal] = None
    available_quantity: Decimal
    minimum_stock: Optional[Decimal] = None
    supplier: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    available_quantity: Optional[Decimal] = None
    cost_per_kg: Optional[Decimal] = None
    color: Optional[str] = None
    minimum_stock: Optional[Decimal] = None
    supplier: Optional[str] = None


class MaterialResponse(MaterialBase):
    id: int
    
    class Config:
        from_attributes = True


class EquipmentBase(BaseModel):
    name: str
    process_type: ProcessType
    capacity_per_hour: Optional[Decimal] = None
    setup_time_minutes: Optional[int] = None
    is_available: bool = True
    specifications: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    capacity_per_hour: Optional[Decimal] = None
    setup_time_minutes: Optional[int] = None
    is_available: Optional[bool] = None
    specifications: Optional[str] = None


class EquipmentResponse(EquipmentBase):
    id: int
    maintenance_schedule: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProductionOrderBase(BaseModel):
    order_number: str
    product_type: ProductType
    process_type: ProcessType
    material_id: int
    quantity_kg: Decimal
    width_mm: Optional[int] = None
    thickness_mm: Optional[Decimal] = None
    color: Optional[str] = None
    caliber: Optional[str] = None
    order_date: date
    delivery_date: date
    priority: int = 1


class ProductionOrderCreate(ProductionOrderBase):
    pass


class ProductionOrderUpdate(BaseModel):
    equipment_id: Optional[int] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    status: Optional[OrderStatus] = None
    priority: Optional[int] = None


class ProductionOrderResponse(ProductionOrderBase):
    id: int
    equipment_id: Optional[int] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: OrderStatus
    waste_percentage: Optional[Decimal] = None
    actual_waste_kg: Optional[Decimal] = None
    material: Optional[MaterialResponse] = None
    equipment: Optional[EquipmentResponse] = None
    
    class Config:
        from_attributes = True


class ScheduleItem(BaseModel):
    order_id: int
    equipment_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    setup_time_minutes: int
    processing_time_minutes: int
    
    
class OptimizationResult(BaseModel):
    schedule: List[ScheduleItem]
    total_waste_kg: Decimal
    total_processing_time_hours: Decimal
    equipment_utilization: dict[int, float]
    waste_reduction_percentage: float
    makespan_hours: float
    optimization_time_seconds: float 