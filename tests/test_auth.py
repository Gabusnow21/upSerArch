import pytest


@pytest.mark.asyncio
async def test_login_page(client):
    response = await client.get("/login")
    assert response.status_code == 200
    assert "Iniciar Sesión" in response.text


@pytest.mark.asyncio
async def test_login_success(client):
    response = await client.post(
        "/login",
        data={"username": "admin", "password": "changeme123"},
    )
    assert response.status_code == 200
    assert "session_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_credentials(client):
    response = await client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 200
    assert "Credenciales incorrectas" in response.text


@pytest.mark.asyncio
async def test_admin_requires_auth(client):
    response = await client.get("/admin")
    assert response.status_code in [307, 401, 403]


@pytest.mark.asyncio
async def test_admin_with_auth(client, auth_cookies):
    response = await client.get("/admin", cookies=auth_cookies)
    assert response.status_code == 200
    assert "Panel de Administración" in response.text


@pytest.mark.asyncio
async def test_logout(client, auth_cookies):
    response = await client.get("/logout", cookies=auth_cookies)
    assert response.status_code == 307
    assert response.headers["location"] == "/login"
