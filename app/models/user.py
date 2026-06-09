from sqlalchemy import Column, BigInteger, String, Boolean, Enum
from sqlalchemy.orm import relationship
from app.core.db.databases import Base
from app.core.db.models import TimestampMixin
from app.models.enums import GenderEnum, DepartmentEnum, RoleEnum

class User(Base, TimestampMixin):
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
    medical_records = relationship("MedicalRecord", back_populates="user")
