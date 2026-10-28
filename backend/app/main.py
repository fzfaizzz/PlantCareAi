import asyncio
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from app.core.config import Settings
from app.core.errors import PublicError
from app.core.middleware import QuotaService, RequestBoundaryMiddleware
from app.services.model_service import ModelService
from app.services.gemini_service import GeminiService
from app.services.plant_info_service import PlantInfoService
from app.services.analysis_service import AnalysisService
from app.api import health, plants, analysis

logger = logging.getLogger("plantcare")


def create_app(settings: Settings | None = None, *, model_service=None, gemini_service=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(application):
        application.state.settings = settings
        application.state.quotas = QuotaService(settings)
        try:
            await application.state.quotas.start()
        except Exception as exc:
            logger.error("Shared quota initialization failed: %s", type(exc).__name__)
        application.state.model = model_service or ModelService(settings)
        await asyncio.to_thread(application.state.model.load)
        application.state.catalog = PlantInfoService()
        application.state.gemini = gemini_service or GeminiService(settings, application.state.quotas)
        await application.state.gemini.start()
        application.state.analysis = AnalysisService(application.state.model, application.state.gemini, application.state.catalog)
        logger.info(json.dumps({"event": "startup", "model_state": application.state.model.state,
                                "gemini_state": application.state.gemini.state}))
        try:
            yield
        finally:
            await application.state.gemini.close()
            await application.state.quotas.close()
            application.state.model.close()

    application = FastAPI(title="PlantCare AI", version="1.0.0", lifespan=lifespan,
                          docs_url="/docs" if settings.app_env != "production" else None,
                          redoc_url=None)
    application.add_middleware(RequestBoundaryMiddleware, settings=settings)
    application.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=False,
                               allow_methods=["GET", "POST", "OPTIONS"],
                               allow_headers=["Content-Type"], expose_headers=["X-Request-ID", "Retry-After"])

    @application.exception_handler(PublicError)
    async def public_error(request: Request, exc: PublicError):
        return JSONResponse({"code": exc.code, "message": exc.message, "request_id": request.state.request_id},
                            status_code=exc.status_code,
                            headers={"Retry-After": str(exc.retry_after)} if exc.retry_after else None)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc):
        return JSONResponse({"code": "invalid_request", "message": "The request does not match the API format.",
                             "request_id": request.state.request_id}, status_code=422)

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc):
        return JSONResponse({"code": "invalid_request" if exc.status_code < 500 else "service_error",
                             "message": "The request could not be processed." if exc.status_code >= 500 else str(exc.detail),
                             "request_id": request.state.request_id}, status_code=exc.status_code)

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exc):
        logger.error("Unhandled request failure: %s", type(exc).__name__)
        return JSONResponse({"code": "internal_error", "message": "The service could not process the request.",
                             "request_id": getattr(request.state, "request_id", "unknown")}, status_code=500)

    for route in (health.router, plants.router, analysis.router):
        application.include_router(route, prefix="/api")
    return application


app = create_app()
