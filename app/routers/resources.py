from fastapi import APIRouter, Depends
from app.dependencies import require_permission

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/")
async def list_resources(_=Depends(require_permission("resource", "read"))):
    return [
        {"id": 1, "name": "Project Alpha"},
        {"id": 2, "name": "Project Beta"},
        {"id": 3, "name": "Project Gamma"},
    ]
