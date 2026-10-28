from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    state = request.app.state
    return {
        "status": "ok", "schema_version": "1.0",
        "model": {"ready": state.model.ready, "state": state.model.state, "error_code": state.model.error_code},
        "gemini": state.gemini.health(),
        "limits": {"max_upload_bytes": state.settings.max_upload_bytes,
                   "max_concurrent_analyses": state.settings.max_concurrent_analyses,
                   "quota_scope": "shared_redis" if state.quotas.redis else "per_process"},
        "privacy": {
            "image_retention": "Images are processed temporarily and are not retained or added to training.",
            "gemini": "When enabled, a metadata-stripped resized image is sent to Google for interpretation.",
            "google_terms_url": "https://ai.google.dev/gemini-api/terms",
        },
    }


@router.get("/ready")
async def ready(request: Request):
    model = request.app.state.model
    return JSONResponse({"ready": model.ready, "model_state": model.state, "request_id": request.state.request_id},
                        status_code=200 if model.ready else 503)


@router.get("/model-info")
async def model_info(request: Request):
    return request.app.state.model.public_info()
