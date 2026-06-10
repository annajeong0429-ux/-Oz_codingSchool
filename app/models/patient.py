from sqlalchemy import Column, BigInteger, SmallInteger, String, Enum
from sqlalchemy.orm import relationship
from app.core.db.databases import Base
from app.core.db.models import TimestampMixin
from app.models.enums import GenderEnum

class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False)
    age = Column(SmallInteger, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    phone = Column(String(11), nullable=False)

    medical_records = relationship(
        "MedicalRecord",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
