from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import home_routes
from app.core.logging import configure_logging
from app.core.settings import settings
from app.db import models
from app.db.database import engine

configure_logging()


def _allowed_origins() -> list[str]:
    return settings.allowed_origins


@asynccontextmanager
async def lifespan(_: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Home Energy Advisor", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home_routes.router, prefix="/api/homes")


@app.get("/")
def root():
    return {"message": "Home Energy Advisor API"}
