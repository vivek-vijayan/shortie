import pytest
from httpx import AsyncClient
from src.app import app
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.mark.asyncio
async def test_homepage():
    async with AsyncClient(app=app, base_url="http://test") as ac: # type: ignore
        response = await ac.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_generate_with_valid_url(monkeypatch): # type: ignore
    # Mock Mongo methods
    async def mock_is_url_present(url, collection): return {"exist": False}
    async def mock_insert(data, collection): return None
    monkeypatch.setattr("src.modules.db.MongoEngine.is_url_present", mock_is_url_present) # type: ignore
    monkeypatch.setattr("src.modules.db.MongoEngine.insert_into_collection", mock_insert)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/generate", data={"org_url": "https://example.com"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_generate_with_empty_url():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/generate", data={"org_url": ""})
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_redirect_valid(monkeypatch):
    async def mock_get_original(short_url, collection):
        return {"exist": True, "original_url": "https://example.com"}

    monkeypatch.setattr("src.modules.db.MongoEngine.get_original_url_from_short_url", mock_get_original)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/valid123", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "https://example.com"


@pytest.mark.asyncio
async def test_redirect_invalid(monkeypatch):
    async def mock_get_original(short_url, collection):
        return {"exist": False}

    monkeypatch.setattr("src.modules.db.MongoEngine.get_original_url_from_short_url", mock_get_original) # type: ignore

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/invalid")
    assert response.status_code == 404
    assert response.json()["message"] == "Invalid short URL"
