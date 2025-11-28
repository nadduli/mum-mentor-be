import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from api.db.database import get_db, Base
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
import uuid

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user():
    return User(id=uuid.uuid4(), email="test@example.com", is_active=True)

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

def test_create_category_success(client):
    """
    Test that a valid category is created successfully with a 201 status.
    """
    payload = {
        "name": "Artificial Intelligence"
    }
    response = client.post("/api/v1/resources/categories", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Category created successfully"
    assert data["data"]["name"] == "Artificial Intelligence"
    assert "id" in data["data"]

def test_create_duplicate_category_fails(client):
    """
    Test that creating a category with a name that already exists returns 400.
    """
    unique_name = f"Data Science {uuid.uuid4()}"
    payload = {
        "name": unique_name
    }
    
    response_1 = client.post("/api/v1/resources/categories", json=payload)
    assert response_1.status_code == 201

    response_2 = client.post("/api/v1/resources/categories", json=payload)
    
    assert response_2.status_code == 400
    

def test_create_resource_success(client):
    """
    Test creating a resource with a valid existing category_id.
    """
    cat_payload = {"name": f"Cloud Computing {uuid.uuid4()}"}
    cat_response = client.post("/api/v1/resources/categories", json=cat_payload)
    category_id = cat_response.json()["data"]["id"]

    resource_payload = {
        "title": "Intro to Kubernetes",
        "content": "Kubernetes is a container orchestration tool...",
        "category_id": category_id
    }
    
    response = client.post("/api/v1/resources/", json=resource_payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Resource created successfully"
    assert data["data"]["title"] == "Intro to Kubernetes"
    assert data["data"]["category_id"] == category_id

def test_create_resource_with_invalid_category_fails(client):
    """
    Test that providing a category_id that does not exist in the DB returns 404.
    """
    invalid_category_id = str(uuid.uuid4())
    
    resource_payload = {
        "title": "Orphan Resource",
        "content": "This should fail because the category doesn't exist",
        "category_id": invalid_category_id
    }
    
    response = client.post("/api/v1/resources/", json=resource_payload)
    
    assert response.status_code == 404

def test_delete_resource_success(client):
    """
    Test deleting an existing resource by ID.
    """
    cat_payload = {"name": f"Cybersecurity {uuid.uuid4()}"}
    cat_response = client.post("/api/v1/resources/categories", json=cat_payload)
    category_id = cat_response.json()["data"]["id"]

    resource_payload = {
        "title": "Network Security Basics",
        "content": "Understanding firewalls and VPNs...",
        "category_id": category_id
    }
    
    resource_response = client.post("/api/v1/resources/", json=resource_payload)
    resource_id = resource_response.json()["data"]["id"]

    delete_response = client.delete(f"/api/v1/resources/{resource_id}")
    
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["message"] == "Resource deleted successfully"
def test_delete_nonexistent_resource_fails(client):
    """
    Test that deleting a resource with an ID that does not exist returns 404.
    """
    nonexistent_resource_id = str(uuid.uuid4())
    
    response = client.delete(f"/api/v1/resources/{nonexistent_resource_id}")
    
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Resource not found"

def test_update_resource_success(client):
    """
    Test updating an existing resource.
    """
    cat_payload = {"name": f"DevOps {uuid.uuid4()}"}
    cat_response = client.post("/api/v1/resources/categories", json=cat_payload)
    category_id = cat_response.json()["data"]["id"]

    resource_payload = {
        "title": "CI/CD Pipelines",
        "content": "Continuous Integration and Continuous Deployment...",
        "category_id": category_id
    }
    
    resource_response = client.post("/api/v1/resources/", json=resource_payload)
    resource_id = resource_response.json()["data"]["id"]

    update_payload = {
        "title": "Advanced CI/CD Pipelines",
        "content": "In-depth look at CI/CD tools and practices...",
        "category_id": category_id
    }
    
    update_response = client.patch(f"/api/v1/resources/{resource_id}", json=update_payload)
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["message"] == "Resource updated successfully"
    assert data["data"]["title"] == "Advanced CI/CD Pipelines"

import uuid
import pytest

# --- CATEGORY TESTS ---

def test_category_lifecycle(client):
    """
    Tests the full lifecycle of a category: Create -> Get -> Update -> Delete
    """
    # 1. Create
    create_payload = {"name": "Lifecycle Test Category"}
    create_resp = client.post("/api/v1/resources/categories", json=create_payload)
    assert create_resp.status_code == 201
    category_id = create_resp.json()["data"]["id"]

    # 2. Get One
    get_resp = client.get(f"/api/v1/resources/categories/{category_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["name"] == "Lifecycle Test Category"

    # 3. Update
    update_payload = {"name": "Updated Category Name"}
    update_resp = client.patch(f"/api/v1/resources/categories/{category_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["name"] == "Updated Category Name"

    # 4. Delete
    delete_resp = client.delete(f"/api/v1/resources/categories/{category_id}")
    assert delete_resp.status_code == 200

    # 5. Verify Deletion (Get One should now fail)
    check_resp = client.get(f"/api/v1/resources/categories/{category_id}")
    assert check_resp.status_code == 404

def test_get_all_categories(client):
    """Test fetching the list of all categories."""
    # Create two categories to ensure list isn't empty
    client.post("/api/v1/resources/categories", json={"name": f"Cat A {uuid.uuid4()}"})
    client.post("/api/v1/resources/categories", json={"name": f"Cat B {uuid.uuid4()}"})

    response = client.get("/api/v1/resources/categories")
    assert response.status_code == 200
    data = response.json()["data"]["categories"]
    assert isinstance(data, list)
    assert len(data) >= 2

def test_update_category_duplicate_name_fails(client):
    """Test that updating a category to a name that already exists fails."""
    # Setup: Create two categories
    c1 = client.post("/api/v1/resources/categories", json={"name": "Cat One"}).json()["data"]
    c2 = client.post("/api/v1/resources/categories", json={"name": "Cat Two"}).json()["data"]

    # Try to rename Cat Two to "Cat One"
    response = client.patch(f"/api/v1/resources/categories/{c2['id']}", json={"name": "Cat One"})
    
    assert response.status_code == 400
    assert "already exists" in response.json()["message"]

# --- RESOURCE LIFECYCLE TESTS ---

def test_resource_crud_lifecycle(client):
    """
    Tests the full lifecycle of a resource: Create -> Get -> Update -> Delete
    """
    # Setup: Create a Category
    cat_resp = client.post("/api/v1/resources/categories", json={"name": f"CRUD Cat {uuid.uuid4()}"})
    cat_id = cat_resp.json()["data"]["id"]

    # 1. Create Resource
    res_payload = {
        "title": "Original Title",
        "content": "Original Content",
        "category_id": cat_id
    }
    create_resp = client.post("/api/v1/resources/", json=res_payload)
    assert create_resp.status_code == 201
    resource_id = create_resp.json()["data"]["id"]

    # 2. Get One Resource
    get_resp = client.get(f"/api/v1/resources/{resource_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["title"] == "Original Title"

    # 3. Update Resource
    update_payload = {
        "title": "New Title",
        "content": "New Content"
    }
    update_resp = client.patch(f"/api/v1/resources/{resource_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["title"] == "New Title"

    # 4. Delete Resource
    delete_resp = client.delete(f"/api/v1/resources/{resource_id}")
    assert delete_resp.status_code == 200

    # 5. Verify Deletion
    check_resp = client.get(f"/api/v1/resources/{resource_id}")
    assert check_resp.status_code == 404

# --- SEARCH AND FILTER TESTS ---

def test_search_resources(client):
    """
    Test searching by title, content, and category name.
    """
    # Setup: Create Data
    # Category: "Programming"
    cat_prog = client.post("/api/v1/resources/categories", json={"name": "Programming"}).json()["data"]
    # Category: "Cooking"
    cat_cook = client.post("/api/v1/resources/categories", json={"name": "Cooking"}).json()["data"]

    # Resource 1: Title="Python Basics", Content="Code", Cat="Programming"
    client.post("/api/v1/resources/", json={"title": "Python Basics", "content": "Code stuff", "category_id": cat_prog["id"]})
    # Resource 2: Title="Pasta Recipe", Content="Boil water", Cat="Cooking"
    client.post("/api/v1/resources/", json={"title": "Pasta Recipe", "content": "Boil water", "category_id": cat_cook["id"]})
    # Resource 3: Title="Java Guide", Content="More Code", Cat="Programming"
    client.post("/api/v1/resources/", json={"title": "Java Guide", "content": "More Code", "category_id": cat_prog["id"]})

    # Test 1: Search by Title ("Python") -> Expect 1
    resp_title = client.get("/api/v1/resources/search?q=Python")
    assert resp_title.status_code == 200
    assert len(resp_title.json()["data"]) == 1
    assert resp_title.json()["data"][0]["title"] == "Python Basics"

    # Test 2: Search by Content ("Boil") -> Expect 1
    resp_content = client.get("/api/v1/resources/search?q=Boil")
    assert resp_content.status_code == 200
    assert len(resp_content.json()["data"]) == 1
    assert resp_content.json()["data"][0]["title"] == "Pasta Recipe"

    # Test 3: Search by Category Name ("Programming") -> Expect 2 (Python + Java)
    resp_cat = client.get("/api/v1/resources/search?q=Programming")
    assert resp_cat.status_code == 200
    assert len(resp_cat.json()["data"]) == 2

def test_search_with_category_filter(client):
    """Test searching with a text query AND a specific category ID."""
    # Setup
    cat_tech = client.post("/api/v1/resources/categories", json={"name": "Tech"}).json()["data"]
    cat_news = client.post("/api/v1/resources/categories", json={"name": "News"}).json()["data"]

    # Both have "Daily" in the title
    client.post("/api/v1/resources/", json={"title": "Daily Tech", "content": "x", "category_id": cat_tech["id"]})
    client.post("/api/v1/resources/", json={"title": "Daily News", "content": "y", "category_id": cat_news["id"]})

    # Search "Daily" BUT restrict to "Tech" category
    response = client.get(f"/api/v1/resources/search?q=Daily&category_id={cat_tech['id']}")
    
    assert response.status_code == 200
    results = response.json()["data"]
    assert len(results) == 1
    assert results[0]["title"] == "Daily Tech"

def test_get_resources_by_category_endpoint(client):
    """Test GET /categories/{id}/resources"""
    # Setup
    cat = client.post("/api/v1/resources/categories", json={"name": f"Specific Cat {uuid.uuid4()}"}).json()["data"]
    
    # Add 2 resources to this category
    client.post("/api/v1/resources/", json={"title": "Res 1", "content": "x", "category_id": cat["id"]})
    client.post("/api/v1/resources/", json={"title": "Res 2", "content": "y", "category_id": cat["id"]})
    
    # Add 1 resource to a DIFFERENT category
    other_cat = client.post("/api/v1/resources/categories", json={"name": "Other"}).json()["data"]
    client.post("/api/v1/resources/", json={"title": "Res 3", "content": "z", "category_id": other_cat["id"]})

    # Fetch resources for the first category only
    response = client.get(f"/api/v1/resources/categories/{cat['id']}/resources")
    
    assert response.status_code == 200
    results = response.json()["data"]
    assert len(results) == 2
    # Ensure Res 3 is NOT in the list
    titles = [r["title"] for r in results]
    assert "Res 1" in titles
    assert "Res 2" in titles
    assert "Res 3" not in titles