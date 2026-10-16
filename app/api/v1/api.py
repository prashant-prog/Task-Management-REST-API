from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, tasks

api_router = APIRouter()

# Include endpoint routers with their respective prefixes and tags
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
