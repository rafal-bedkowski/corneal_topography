from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings
from app.routers import exams, health, stats
from app.store import IndexStore, IndexUnavailableError


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Corneal Topography API")
    app.state.settings = settings
    app.state.store = IndexStore(settings.index_path)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.exception_handler(IndexUnavailableError)
    def index_unavailable(_: Request, error: IndexUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(error)})

    for router in (health.router, exams.router, stats.router):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
