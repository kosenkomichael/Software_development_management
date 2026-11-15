from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.materials import router as materials_router
from app.api.v1.routers.public_materials import router as public_materials_router
from app.api.v1.routers.public_quizzes import router as public_quizzes_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(materials_router)

api_router.include_router(public_quizzes_router)

api_router.include_router(public_materials_router)
