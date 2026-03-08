from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.session import get_db
from app.schemas.advice import AdviceResponse
from app.schemas.home import HomeCreate, HomeResponse
from app.services import advice as advice_service
from app.services import home as home_service

router = APIRouter(tags=["homes"])


@router.post(
    "", response_model=HomeResponse, status_code=status.HTTP_201_CREATED
)
def create_home(home_data: HomeCreate, db: Session = Depends(get_db)):
    try:
        created_home = home_service.create_home(db, home_data)
        logger.info("Home created successfully: home_id=%s", created_home.id)
        return home_service.serialize_home(created_home)
    except Exception:
        logger.exception("Failed to create home")
        raise HTTPException(status_code=500, detail="Failed to create home")


@router.get("/{home_id}", response_model=HomeResponse)
def get_home(home_id: int, db: Session = Depends(get_db)):
    db_home = home_service.get_home(db, home_id)

    if not db_home:
        logger.warning("Home not found: home_id=%s", home_id)
        raise HTTPException(status_code=404, detail="Home not found")

    logger.info("Home retrieved successfully: home_id=%s", home_id)
    return home_service.serialize_home(db_home)


@router.post("/{home_id}/advice", response_model=AdviceResponse)
def generate_home_advice(home_id: int, db: Session = Depends(get_db)):
    db_home = home_service.get_home(db, home_id)

    if not db_home:
        logger.warning(
            "Home not found for advice generation: home_id=%s", home_id
        )
        raise HTTPException(status_code=404, detail="Home not found")

    try:
        logger.info("Generating fresh advice for home_id=%s", home_id)
        return advice_service.get_advice(db_home, db)
    except RuntimeError as e:
        logger.exception("Failed to generate advice for home_id=%s", home_id)
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        logger.exception(
            "Unexpected error while generating advice for home_id=%s", home_id
        )
        raise HTTPException(
            status_code=500, detail="Unexpected error while generating advice"
        )
