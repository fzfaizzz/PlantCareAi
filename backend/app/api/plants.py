from fastapi import APIRouter, Request
from app.core.errors import PublicError

router = APIRouter()


@router.get("/plants")
async def plants(request: Request):
    state = request.app.state
    return {"schema_version": "1.0", "items": state.catalog.list(state.model.labels),
            "model_ready": state.model.ready}


@router.get("/plants/{slug}")
async def plant(slug: str, request: Request):
    state = request.app.state
    item = state.catalog.get_slug(slug, state.model.labels)
    if item is None:
        raise PublicError(404, "plant_not_found", "This condition-information entry was not found.")
    return item
