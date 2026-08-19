import pytest
from io import BytesIO


@pytest.mark.asyncio
async def test_upload_requires_auth(client):
    pdf_content = b"%PDF-1.4 test content"
    response = await client.post(
        "/upload",
        files={"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")},
        data={"codigo": "test-001"},
    )
    assert response.status_code in [307, 401, 403]


@pytest.mark.asyncio
async def test_upload_pdf_success(client, auth_cookies):
    pdf_content = b"%PDF-1.4 test content"
    response = await client.post(
        "/upload",
        files={"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")},
        data={"codigo": "test-001"},
        cookies=auth_cookies,
    )
    assert response.status_code == 200
    assert "test-001" in response.text


@pytest.mark.asyncio
async def test_upload_non_pdf_rejected(client, auth_cookies):
    txt_content = b"This is not a PDF"
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", BytesIO(txt_content), "text/plain")},
        data={"codigo": "test-002"},
        cookies=auth_cookies,
    )
    assert response.status_code == 200
    assert "Solo se permiten archivos PDF" in response.text


@pytest.mark.asyncio
async def test_upload_overwrites_existing_code(client, auth_cookies):
    pdf_content = b"%PDF-1.4 first version"
    await client.post(
        "/upload",
        files={"file": ("test1.pdf", BytesIO(pdf_content), "application/pdf")},
        data={"codigo": "overwrite-test"},
        cookies=auth_cookies,
    )

    pdf_content_2 = b"%PDF-1.4 second version"
    response = await client.post(
        "/upload",
        files={"file": ("test2.pdf", BytesIO(pdf_content_2), "application/pdf")},
        data={"codigo": "overwrite-test"},
        cookies=auth_cookies,
    )
    assert response.status_code == 200
    assert "actualizado" in response.text
