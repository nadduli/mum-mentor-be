import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from main import app
from api.v1.models.user.user import User
from api.v1.models.community.posts import Post
from api.db.database import get_db
from api.utils.deps import get_current_user

client = TestClient(app)


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


def _make_user():
    return User(
        id=str(uuid.uuid4()),
        email="poster@example.com",
        full_name="Poster",
        role="user",
        password_hash="hash",
        is_active=True,
    )


def _make_post(user_id=None):
    return Post(
        id=uuid.UUID(int=1),
        user_id=user_id or uuid.uuid4(),
        title="Hello World",
        content="This is my first post",
        created_at=datetime.now(timezone.utc),
        views=0,
    )


def test_create_post_success(mock_db_session, monkeypatch):
    user = _make_user()
    app.dependency_overrides[get_current_user] = lambda: user

    post_obj = _make_post(user_id=uuid.UUID(user.id))

    monkeypatch.setattr(
        "api.v1.services.community_posts.CommunityPostService.create_post",
        lambda self, user_id, payload: (post_obj, None),
    )

    payload = {"title": post_obj.title, "content": post_obj.content}
    response = client.post("/api/v1/community/posts/", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert "data" in body
    assert body["data"]["title"] == post_obj.title
    assert body["data"]["content"] == post_obj.content


def test_create_post_invalid_payload_missing_title(mock_db_session):
    # ensure auth so validation runs after auth
    app.dependency_overrides[get_current_user] = lambda: _make_user()

    response = client.post("/api/v1/community/posts/", json={"content": "x"})
    assert response.status_code == 422


def test_create_post_title_too_long(mock_db_session):
    app.dependency_overrides[get_current_user] = lambda: _make_user()

    long_title = "x" * 201
    response = client.post("/api/v1/community/posts/", json={"title": long_title, "content": "ok"})
    assert response.status_code == 422


def test_create_post_no_auth(mock_db_session):
    # Do not override get_current_user -> should be unauthorized
    response = client.post("/api/v1/community/posts/", json={"title": "x", "content": "y"})
    assert response.status_code == 401


def test_create_post_server_error(mock_db_session, monkeypatch):
    user = _make_user()
    app.dependency_overrides[get_current_user] = lambda: user

    monkeypatch.setattr(
        "api.v1.services.community_posts.CommunityPostService.create_post",
        lambda self, user_id, payload: (None, (500, "Failed to create post")),
    )

    response = client.post("/api/v1/community/posts/", json={"title": "x", "content": "y"})
    assert response.status_code == 500
