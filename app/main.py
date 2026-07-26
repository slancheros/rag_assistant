from contextlib import asynccontextmanager
from collections.abc import Callable, Awaitable
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import (
    bind_request_id,
    configure_logging,
    reset_request_id,
)
from app.dependencies import Container, build_container


logger = logging.getLogger(__name__)


ContainerBuilder = Callable[
    [],
    Awaitable[Container],
]


def create_app(
    container_builder: ContainerBuilder | None = None,
) -> FastAPI:
    async def default_builder() -> Container:
        settings = get_settings()
        return await build_container(settings)

    selected_builder = (
        container_builder or default_builder
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = get_settings()
        configure_logging(settings.log_level)
        app.state.settings = settings
        logger.info(
            "application_starting",
            extra={
                "provider": settings.ai_provider,
                "llm_model": settings.llm_model,
                "embedding_model": settings.embedding_model,
            },
        )
        app.state.container = (
            await selected_builder()
        )
        logger.info("application_ready")
        yield
        logger.info("application_stopping")

    application = FastAPI(
        title="NimbusCloud Support Assistant",
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next,
    ):
        request_id = str(uuid4())
        request.state.request_id = request_id
        token = bind_request_id(request_id)
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "http_request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(
                        (perf_counter() - started_at) * 1000,
                        2,
                    ),
                },
            )
            raise
        else:
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "http_request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(
                        (perf_counter() - started_at) * 1000,
                        2,
                    ),
                },
            )
            return response
        finally:
            reset_request_id(token)

    application.include_router(
        router,
        prefix="/api/v1",
    )

    application.mount(
        "/",
        StaticFiles(directory="app/static", html=True),
        name="ui",
    )

    @application.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": getattr(
                        request.state,
                        "request_id",
                        None,
                    ),
                }
            },
        )

    return application


app = create_app()
