"""The HTTP API in front of the library engine (Phase 4)."""

from fastapi import FastAPI

app = FastAPI(title="LibraryHub Mini")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}