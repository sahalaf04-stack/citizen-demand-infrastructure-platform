from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class District(Base):
    """
    Reference table standing in for fused government datasets:
    demographic data (population) + infrastructure indices (infra_deficit_score,
    0-1, higher = more underserved) + investment context (planned_budget_cr).
    In production this table is populated from SDG India Index / Gati Shakti /
    census exports rather than hardcoded.
    """
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    state = Column(String)
    population = Column(Integer)
    infra_deficit_score = Column(Float)  # 0-1, higher = worse existing infra
    planned_budget_cr = Column(Float)    # already-allocated budget, crore INR
    lat = Column(Float)
    lon = Column(Integer)

    requests = relationship("CitizenRequest", back_populates="district")


class CitizenRequest(Base):
    __tablename__ = "citizen_requests"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(String)
    language = Column(String)          # e.g. "hi", "kn", "en"
    translated_text = Column(String)
    category = Column(String)          # road | water | electricity | sanitation | other
    urgency = Column(String)           # low | medium | high
    lat = Column(Float)
    lon = Column(Float)
    district_id = Column(Integer, ForeignKey("districts.id"))
    cluster_id = Column(Integer, nullable=True)  # set by dedup step
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    district = relationship("District", back_populates="requests")
