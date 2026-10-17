from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# Endpoints implemented in AUTH-2:
# POST /auth/register
# POST /auth/login
# POST /auth/refresh
# POST /auth/logout
