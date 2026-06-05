from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db.databases import Base
from datetime import datetime

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id = Column(BigInteger, ForeignKey("patients.id"), nullable=False)
    chart_number = Column(String(50), unique=True, nullable=False)
    symptoms = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

    patient = relationship("Patient", back_populates="medical_records")
    user = relationship("User", back_populates="medical_records")
    xray_images = relationship("XrayImage", back_populates="medical_record")
    ai_analysis_results = relationship("AiAnalysisResult", back_populates="medical_record")