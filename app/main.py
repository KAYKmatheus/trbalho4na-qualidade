"""Application entrypoint for the academic reservation system."""

import logging
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import app

STATIC_DIRECTORY = Path(__file__).resolve().parent / "web" / "static"
if not any(getattr(route, "name", None) == "web" for route in app.router.routes):
    app.mount("/app", StaticFiles(directory=str(STATIC_DIRECTORY)), name="web")


def redirect_to_web_app() -> RedirectResponse:
    return RedirectResponse(url="/app/index.html", status_code=307)


if not any(getattr(route, "name", None) == "redirect_to_web_app" for route in app.router.routes):
    app.add_api_route("/", redirect_to_web_app, methods=["GET"], include_in_schema=False)


@app.exception_handler(Exception)
async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
    logging.exception(
        "Unhandled exception while processing request",
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor."},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
