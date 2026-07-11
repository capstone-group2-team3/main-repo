from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.database import Base, engine
from app.db import models, severity_models  # noqa: F401
from app.services.severity_classifier_service import severity_service


app = FastAPI(
    title="MedDx Assistant API",
    description="Doctor-facing clinical decision support API for educational Capstone use decision support API for educational Capstone use.",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    severity_service.initialize()


app.include_router(router)
