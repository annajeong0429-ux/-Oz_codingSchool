from sqlalchemy import Column, BigInteger, Boolean, Numeric, String, Text, ForeignKey   # Text 추가
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from app.core.db.databases import Base
from app.core.db.models import TimestampMixin

class AiAnalysisResult(Base, TimestampMixin):
    __tablename__ = "ai_analysis_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, ForeignKey("medical_records.id", ondelete="CASCADE"), nullable=False)
    is_pneumonia = Column(Boolean, nullable=False)
    confidence = Column(Numeric(5, 2), nullable=False)
    heatmap_url = Column(MEDIUMTEXT, nullable=True)   # Text(64KB) → MEDIUMTEXT(16MB): 컬러 오버레이 base64 수용
    ai_model = Column(String(50), nullable=False)

    medical_record = relationship("MedicalRecord", back_populates="ai_analysis_results")