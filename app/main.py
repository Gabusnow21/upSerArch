from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings, ensure_directories
from app.database import engine, Base
from app.routers import pages, upload, download


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directories()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="upSerArch", lifespan=lifespan)

templates = Jinja2Templates(directory="app/templates")

app.include_router(pages.router)
app.include_router(upload.router)
app.include_router(download.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
