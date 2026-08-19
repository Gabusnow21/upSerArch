import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_auth
from app.config import settings
from app.database import get_session
from app.models import FileRecord

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    codigo: str = Form(...),
    session: AsyncSession = Depends(get_session),
    username: str = Depends(require_auth),
):
    errors = []

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        errors.append("Solo se permiten archivos PDF")

    if not codigo.strip():
        errors.append("El código es obligatorio")

    if errors:
        return templates.TemplateResponse(
            request, "components/upload_result.html",
            {"success": False, "errors": errors, "codigo": codigo},
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    existing = await session.execute(
        select(FileRecord).where(FileRecord.codigo == codigo.strip())
    )
    existing_record = existing.scalar_one_or_none()

    if existing_record:
        old_file = upload_dir / existing_record.stored_filename
        if old_file.exists():
            old_file.unlink()

        stored_name = f"{uuid.uuid4().hex}.pdf"
        file_path = upload_dir / stored_name

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        existing_record.original_filename = file.filename
        existing_record.stored_filename = stored_name
        existing_record.file_size = len(content)

        await session.commit()

        return templates.TemplateResponse(
            request, "components/upload_result.html",
            {
                "success": True,
                "message": f"Archivo actualizado para el código '{codigo}'",
                "codigo": codigo,
            },
        )

    stored_name = f"{uuid.uuid4().hex}.pdf"
    file_path = upload_dir / stored_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    record = FileRecord(
        codigo=codigo.strip(),
        original_filename=file.filename,
        stored_filename=stored_name,
        file_size=len(content),
    )
    session.add(record)
    await session.commit()

    return templates.TemplateResponse(
        request, "components/upload_result.html",
        {
            "success": True,
            "message": f"Archivo subido correctamente con el código '{codigo}'",
            "codigo": codigo,
        },
    )
