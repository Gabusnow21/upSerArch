from fastapi import Depends, HTTPException, Request, Response
from itsdangerous import TimedSerializer

from app.config import settings

serializer = TimedSerializer(settings.SECRET_KEY)

COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 86400  # 24 hours


def create_session_token(username: str) -> str:
    return serializer.dumps(username)


def verify_session_token(token: str) -> str | None:
    try:
        return serializer.loads(token, max_age=COOKIE_MAX_AGE)
    except Exception:
        return None


def set_session_cookie(response: Response, username: str):
    token = create_session_token(username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )


def clear_session_cookie(response: Response):
    response.delete_cookie(key=COOKIE_NAME)


async def require_auth(request: Request) -> str:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=307, headers={"Location": "/login"})
    username = verify_session_token(token)
    if not username:
        raise HTTPException(status_code=307, headers={"Location": "/login"})
    return username
