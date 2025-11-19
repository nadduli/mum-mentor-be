import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api.v1.routes.faq.faq import router as faq_router
from api.v1.services.faq.faq import FAQService


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(faq_router)
    return TestClient(app)


def test_get_faqs_success(client):
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

    with patch.object(FAQService, "fetch_faqs", Mock(return_value=mock_data)):
        response = client.get("/faqs")

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["question"] == "Mock question?"


def test_get_faqs_incorrect_input(client):
    response = client.get("/faqs?limit=-5")

    assert response.status_code == 422
    assert "greater than" in response.json()["detail"][0]["msg"].lower()


def test_get_faqs_expected_error(client):
    with patch.object(FAQService, "fetch_faqs", Mock(side_effect=Exception("Boom"))):
        response = client.get("/faqs")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"