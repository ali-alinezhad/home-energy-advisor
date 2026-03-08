from sqlalchemy.orm import Session

from app.db import models
from app.schemas.advice import AdviceResponse
from app.schemas.home import HomeCreate, HomeResponse


def serialize_home(home: models.Home) -> HomeResponse:
    latest_advice = None

    if home.latest_advice:
        latest_advice = AdviceResponse.model_validate_json(home.latest_advice)

    return HomeResponse(
        id=home.id,
        size=home.size,
        year_built=home.year_built,
        heating_type=home.heating_type,
        insulation_level=home.insulation_level,
        latest_advice=latest_advice,
        advice_generated_at=home.advice_generated_at,
    )


def create_home(db: Session, home: HomeCreate):
    db_home = models.Home(
        size=home.size,
        year_built=home.year_built,
        heating_type=home.heating_type,
        insulation_level=home.insulation_level,
    )

    db.add(db_home)
    db.commit()
    db.refresh(db_home)

    return db_home


def get_home(db: Session, home_id: int):
    return db.query(models.Home).filter(models.Home.id == home_id).first()
