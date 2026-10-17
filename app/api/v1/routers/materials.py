from fastapi import APIRouter

router = APIRouter(prefix="/materials", tags=["materials"])

# Endpoints implemented in UPLOAD-3:
# POST   /materials/upload
# GET    /materials/
# GET    /materials/{id}
# GET    /materials/{id}/notes
# GET    /materials/{id}/notes/status
# GET    /materials/{id}/quiz
# GET    /materials/{id}/quiz/status
# POST   /materials/{id}/quiz/submit
