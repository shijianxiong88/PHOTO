from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.web.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="家庭出游相册")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(router)
    return app


app = create_app()
