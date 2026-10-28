import asyncio
import time
from fastapi import APIRouter, Request
from fastapi.responses import Response
from starlette.datastructures import UploadFile
from starlette.concurrency import run_in_threadpool
from app.core.errors import PublicError
from app.schemas.analysis import AnalysisResponse
from app.services.image_service import normalize_image

router = APIRouter()


async def wait_for_disconnect(request):
    while True:
        message = await request.receive()
        if message["type"] == "http.disconnect":
            return


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: Request):
    state = request.app.state
    address = request.client.host if request.client else "unknown"
    if state.settings.trust_proxy_headers:
        address = request.headers.get("x-forwarded-for", address).split(",")[0].strip()
    await state.quotas.take_request(address)
    if not request.headers.get("content-type", "").lower().startswith("multipart/form-data"):
        raise PublicError(415, "multipart_required", "Send one image using multipart field 'image'.")
    started = time.perf_counter()
    async with request.form(max_files=1, max_fields=0, max_part_size=64 * 1024) as form:
        image_file = form.get("image")
        if len(form) != 1 or not isinstance(image_file, UploadFile):
            raise PublicError(422, "image_required", "Provide exactly one image in multipart field 'image'.")
        data = await image_file.read(state.settings.max_upload_bytes + 1)
        image = await run_in_threadpool(normalize_image, data, state.settings)
    decode_ms = (time.perf_counter() - started) * 1000
    if not state.model.ready:
        raise PublicError(503, "model_unavailable", "The trained model is unavailable. Install and verify a trained model bundle before analysis.")
    task = asyncio.create_task(state.analysis.analyze(image, request.state.request_id, decode_ms))
    disconnected = asyncio.create_task(wait_for_disconnect(request))
    try:
        done, _ = await asyncio.wait({task, disconnected}, timeout=state.settings.analysis_timeout_seconds,
                                     return_when=asyncio.FIRST_COMPLETED)
        if task in done:
            return await task
        if disconnected in done:
            return Response(status_code=499)
        raise PublicError(504, "analysis_timeout", "Analysis timed out. Please try again.")
    finally:
        # Cancels optional network work; already-running native TF inference owns its
        # bounded worker slot until completion. Late results can never reach the client.
        task.cancel()
        disconnected.cancel()
        await asyncio.gather(task, disconnected, return_exceptions=True)
