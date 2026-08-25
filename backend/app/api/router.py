from fastapi import APIRouter

from app.analytics.router import router as analytics_router
from app.api.routes.machines import router as machines_router
from app.api.routes.pcb_units import router as pcb_units_router
from app.api.routes.process_events import (
    router as process_events_router,
)
from app.api.routes.production_orders import (
    router as production_orders_router,
)
from app.api.routes.quality_measurements import (
    router as quality_measurements_router,
)
from app.api.routes.users import router as users_router
from app.auth.router import router as auth_router


api_router = APIRouter(
    prefix="/api/v1",
)

api_router.include_router(machines_router)
api_router.include_router(production_orders_router)
api_router.include_router(pcb_units_router)
api_router.include_router(process_events_router)
api_router.include_router(quality_measurements_router)
api_router.include_router(analytics_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)