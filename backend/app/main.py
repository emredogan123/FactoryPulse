from fastapi import FastAPI, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.machines import router as machines_router
from app.core.config import settings
from app.db.session import check_database_connection
from app.api.routes.production_orders import (
    router as production_orders_router,
)

from app.api.routes.pcb_units import router as pcb_units_router

app = FastAPI(
    title=f"{settings.app_name} API",
    description="Manufacturing quality and process intelligence platform",
    version="0.1.0",
)

app.include_router(machines_router)
app.include_router(production_orders_router)
app.include_router(pcb_units_router)

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to FactoryPulse API",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "factorypulse-api",
        "version": "0.1.0",
    }


@app.get("/health/database", tags=["Health"])
def database_health_check() -> dict[str, str]:
    try:
        check_database_connection()
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from error

    return {
        "status": "healthy",
        "database": "connected",
    }