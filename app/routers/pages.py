from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_auth, set_session_cookie, clear_session_cookie
from app.config import settings
from app.database import get_session
from app.models import FileRecord

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
):
    if username == settings.ADMIN_USER and password == settings.ADMIN_PASS:
        response = templates.TemplateResponse(
            request, "components/login_result.html", {"success": True}
        )
        set_session_cookie(response, username)
        return response

    return templates.TemplateResponse(
        request, "components/login_result.html",
        {"success": False, "error": "Credenciales incorrectas"},
    )


@router.get("/logout")
async def logout():
    response = Response(status_code=307, headers={"Location": "/login"})
    clear_session_cookie(response)
    return response


@router.get("/admin", response_class=HTMLResponse)
async def admin(
    request: Request,
    session: AsyncSession = Depends(get_session),
    username: str = Depends(require_auth),
):
    result = await session.execute(select(FileRecord).order_by(FileRecord.upload_date.desc()))
    files = result.scalars().all()
    return templates.TemplateResponse(
        request, "admin.html", {"files": files, "username": username}
    )


@router.delete("/admin/{file_id}")
async def delete_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
    username: str = Depends(require_auth),
):
    result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
    record = result.scalar_one_or_none()

    if not record:
        return Response(status_code=404)

    file_path = Path(settings.UPLOAD_DIR) / record.stored_filename
    if file_path.exists():
        file_path.unlink()

    await session.delete(record)
    await session.commit()

    return Response(status_code=200, content="")
