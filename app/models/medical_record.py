from sqlalchemy import Column, BigInteger, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db.databases import Base
from app.core.db.models import TimestampMixin

class MedicalRecord(Base, TimestampMixin):
    __tablename__ = "medical_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id = Column(BigInteger, ForeignKey("patients.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    chart_number = Column(String(50), unique=True, nullable=False)
    symptoms = Column(Text, nullable=False)

    patient = relationship("Patient", back_populates="medical_records")
    user = relationship("User", back_populates="medical_records")   # ← 이 줄 추가!
    xray_images = relationship("XrayImage", back_populates="medical_record")
    ai_analysis_results = relationship("AiAnalysisResult", back_populates="medical_record")