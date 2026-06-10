from sqlalchemy import Column, BigInteger, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db.databases import Base
from app.core.db.models import TimestampMixin

class MedicalRecord(Base, TimestampMixin):
    __tablename__ = "medical_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # FK 컬럼 (10, 11번 줄)
    patient_id = Column(BigInteger, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)   # ← nullable True!
    chart_number = Column(String(50), unique=True, nullable=False)
    symptoms = Column(Text, nullable=False)

    # 관계 (아래쪽) — patient/user는 그대로, 자식 둘에 cascade 추가
    patient = relationship("Patient", back_populates="medical_records")
    user = relationship("User", back_populates="medical_records")          # 그대로 (cascade X)
    xray_images = relationship(
        "XrayImage", back_populates="medical_record",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    ai_analysis_results = relationship(
        "AiAnalysisResult", back_populates="medical_record",
        cascade="all, delete-orphan", passive_deletes=True,
    )
