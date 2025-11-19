import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import FastAPI, HTTPException
from unittest.mock import AsyncMock, patch

from api.v1.routes.faq.faq import router as faq_router
from api.v1.services.faq.faq import FAQService


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(faq_router)
    return app



@pytest_asyncio.fixture
async def client(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


# ----------------------------------------------------
# 1. SUCCESSFUL REQUEST (Mocking Service Success)
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_get_faqs_success(client):
    mock_data = (
        [
            {
                "id": "123",
                "category": "general",
                "question": "Mock question?",
                "answer": "Mock answer.",
                "keywords": {},
                "view_count": 0,
                "helpful_count": 0,
                "order_index": 0,
                "created_at": "2025-01-01T00:00:00",
            }
        ],
        1,  # total count
    )

    with patch.object(FAQService, "fetch_faqs", AsyncMock(return_value=mock_data)):
        response = await client.get("/faqs")

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["question"] == "Mock question?"


# ----------------------------------------------------
# 2. INCORRECT INPUT (FastAPI validation)
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_get_faqs_incorrect_input(client):
    response = await client.get("/faqs?limit=-5")

    assert response.status_code == 422  # validation error
    assert response.json()["detail"][0]["msg"].lower().find("greater than") != -1


# ----------------------------------------------------
# 3. EXPECTED ERROR (Simulate Service Failure)
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_get_faqs_expected_error(client):
    with patch.object(FAQService, "fetch_faqs", AsyncMock(side_effect=Exception("Boom"))):
        response = await client.get("/faqs")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"