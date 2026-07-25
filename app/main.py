from contextlib import asynccontextmanager
from collections.abc import Callable, Awaitable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors import AppError
from app.dependencies import Container, build_container


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
        app.state.container = (
            await selected_builder()
        )
        yield

    application = FastAPI(
        title="NimbusCloud Support Assistant",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(
        router,
        prefix="/api/v1",
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