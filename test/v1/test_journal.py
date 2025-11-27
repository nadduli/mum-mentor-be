from fastapi import status
from datetime import datetime

def test_create_journal_success(client, auth_headers):
    """Test creating a journal entry successfully"""
    journal_data = {
        "title": "My Day",
        "date": datetime.utcnow().isoformat(),
        "category": "Sleep",
        "mood": "Happy",
        "photos": ["https://example.com/photo1.jpg"],
        "thoughts": "Today was a great day! I learned a lot about FastAPI."
    }
    
    response = client.post(
        "/api/v1/journal/entry/",
        json=journal_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["message"] == "Journal created successfully"
    assert data["data"]["title"] == journal_data["title"]
    assert "journal_entry_id" in data["data"]

def test_create_journal_unauthorized(client):
    """Test creating a journal entry without authentication"""
    journal_data = {
        "title": "My Day",
        "date": datetime.utcnow().isoformat(),
        "thoughts": "Today was a great day!"
    }
    
    response = client.post(
        "/api/v1/journal/entry/",
        json=journal_data
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_journal_invalid_data(client, auth_headers):
    """Test creating a journal entry with missing required fields"""
    journal_data = {
        "title": "My Day",
        # Missing date and thoughts
    }
    
    response = client.post(
        "/api/v1/journal/entry/",
        json=journal_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
