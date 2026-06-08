from sqlalchemy import Column, BigInteger, Boolean, Numeric, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db.databases import Base
from datetime import datetime

class AiAnalysisResult(Base):
    __tablename__ = "ai_analysis_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, ForeignKey("medical_records.id"), nullable=False)
    is_pneumonia = Column(Boolean, nullable=False)
    confidence = Column(Numeric(5, 2), nullable=False)
    heatmap_url = Column(String(255), nullable=False)
    ai_model = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

    medical_record = relationship("MedicalRecord", back_populates="ai_analysis_results")

    