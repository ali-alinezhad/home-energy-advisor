from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from .database import Base


class Home(Base):
    __tablename__ = "home"

    id = Column(Integer, primary_key=True, index=True)
    size = Column(Integer, nullable=False)
    year_built = Column(Integer, nullable=False)
    heating_type = Column(String, nullable=False)
    insulation_level = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    latest_advice = Column(Text, nullable=True)
    advice_generated_at = Column(DateTime, nullable=True)
