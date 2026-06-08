from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.core.db.databases import Base
import enum
from datetime import datetime

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"

class DepartmentEnum(str, enum.Enum):
    radiology = "radiology"
    internal = "internal"
    emergency = "emergency"

class RoleEnum(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(20))
    phone_number = Column(String(20), unique=True)
    gender = Column(Enum(GenderEnum), nullable=False)
    department = Column(Enum(DepartmentEnum), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

