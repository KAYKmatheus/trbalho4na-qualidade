"""Application entrypoint for the academic reservation system."""

from app.api.v1 import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
