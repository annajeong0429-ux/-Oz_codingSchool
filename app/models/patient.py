from sqlalchemy import Column, BigInteger, SmallInteger, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.core.db.databases import Base
import enum
from datetime import datetime

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"

class Patient(Base):
    __tablename__ = "patients"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False)
    age = Column(SmallInteger, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    phone = Column(String(11), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

    medical_records = relationship("MedicalRecord", back_populates="patient")