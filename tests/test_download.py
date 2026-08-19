import pytest
from io import BytesIO


@pytest.mark.asyncio
async def test_download_nonexistent_code(client):
    response = await client.get("/d/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_success(client, auth_cookies):
    pdf_content = b"%PDF-1.4 test content"
    await client.post(
        "/upload",
        files={"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")},
        data={"codigo": "download-test"},
        cookies=auth_cookies,
    )

    response = await client.get("/d/download-test")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_search_empty(client):
    response = await client.get("/search?q=")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_search_found(client, auth_cookies):
    pdf_content = b"%PDF-1.4 test content"
    await client.post(
        "/upload",
        files={"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")},
        data={"codigo": "search-test"},
        cookies=auth_cookies,
    )

    response = await client.get("/search?q=search-test")
    assert response.status_code == 200
    assert "search-test" in response.text


@pytest.mark.asyncio
async def test_search_not_found(client):
    response = await client.get("/search?q=nonexistent")
    assert response.status_code == 200
    assert "No se encontró" in response.text
