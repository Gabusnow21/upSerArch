from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import FileRecord
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/d/{codigo}")
async def download_file(
    codigo: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(FileRecord).where(FileRecord.codigo == codigo)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    file_path = Path(settings.UPLOAD_DIR) / record.stored_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    return FileResponse(
        path=file_path,
        filename=record.original_filename,
        media_type="application/pdf",
    )


@router.get("/search", response_class=HTMLResponse)
async def search_file(
    request: Request,
    q: str = "",
    session: AsyncSession = Depends(get_session),
):
    if not q.strip():
        return templates.TemplateResponse(
            request, "components/search_result.html",
            {"found": False, "query": q},
        )

    result = await session.execute(
        select(FileRecord).where(FileRecord.codigo == q.strip())
    )
    record = result.scalar_one_or_none()

    if record:
        return templates.TemplateResponse(
            request, "components/search_result.html",
            {
                "found": True,
                "record": record,
                "query": q,
            },
        )

    return templates.TemplateResponse(
        request, "components/search_result.html",
        {"found": False, "query": q},
    )
