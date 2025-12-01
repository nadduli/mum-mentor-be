import pytest
from fastapi.testclient import TestClient
from main import app
from api.utils.limiter import RateLimiter


def test_global_rate_limiter_works():
    """
    Test that rate limiting works correctly.
    """
    rate_limiter = None
    for middleware in app.user_middleware:
        if middleware.cls == RateLimiter:
            rate_limiter = middleware.kwargs
            break
    
    original_limit = None
    if rate_limiter is not None:
        original_limit = rate_limiter.get('limit', '200/minute')
    
    from fastapi import FastAPI
    test_app = FastAPI()
    test_app.add_middleware(RateLimiter, limit="2/minute")
    
    @test_app.get("/")
    async def read_root():
        return {"message": "OK"}
    
    try:
        with TestClient(test_app) as client:
            response1 = client.get("/", headers={"X-Forwarded-For": "203.0.113.1"})
            assert response1.status_code == 200
            response2 = client.get("/", headers={"X-Forwarded-For": "203.0.113.1"})
            assert response2.status_code == 200
            response3 = client.get("/", headers={"X-Forwarded-For": "203.0.113.1"})
            assert response3.status_code == 429
            
            data = response3.json()
            assert data["status"] == "error"
            assert "Rate limit exceeded" in data["message"]
    
    finally:
        pass


def test_different_ips_have_separate_limits():
    """
    Test that different IPs have separate rate limits.
    """
    from fastapi import FastAPI
    test_app = FastAPI()
    test_app.add_middleware(RateLimiter, limit="1/minute")
    
    @test_app.get("/")
    async def read_root():
        return {"message": "OK"}
    
    with TestClient(test_app) as client:
        response1 = client.get("/", headers={"X-Forwarded-For": "203.0.113.10"})
        assert response1.status_code == 200
        
        response2 = client.get("/", headers={"X-Forwarded-For": "203.0.113.20"})
        assert response2.status_code == 200
        
        response3 = client.get("/", headers={"X-Forwarded-For": "203.0.113.10"})
        assert response3.status_code == 429