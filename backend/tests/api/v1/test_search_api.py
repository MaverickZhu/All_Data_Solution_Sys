import pytest
import httpx
from typing import Any, AsyncGenerator
from io import BytesIO
from pathlib import Path

from backend.main import app
from backend.core.database import get_db
from backend.tests.conftest import db_session as test_db_session
from backend.models.user import User
from backend.models.project import Project
from backend.core.config import settings

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio

# We can reuse fixtures from the other test file, or move them to conftest.py
# For now, let's assume they are available or redefined here.

async def test_semantic_search_api(
    async_client: httpx.AsyncClient,
    auth_headers: dict,
    test_project,
    tmp_path: Path,
    monkeypatch
):
    """
    Test the full API flow for semantic search.
    """
    # Override settings for the test
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    
    # 1. Create a text file with known content
    file_content = "A black cat sat comfortably on the red mat."
    file_name = "test_document.txt"
    file_path = tmp_path / file_name
    file_path.write_text(file_content)

    # 2. Upload the file to trigger embedding generation
    upload_url = f"/api/v1/data_sources/upload?project_id={test_project.id}"
    with open(file_path, "rb") as f:
        upload_response = await async_client.post(
            upload_url,
            files={"file": (file_name, f, "text/plain")},
            headers=auth_headers
        )
    assert upload_response.status_code == 201

    # 3. Perform a semantic search with a similar query
    search_url = f"/api/v1/projects/{test_project.id}/search"
    query = "A feline was resting on a rug."
    
    # The embedding process might take a moment even if eager
    # In a real-world scenario with a separate worker, we'd need to poll.
    # Here, eager mode makes it synchronous.
    
    search_response = await async_client.post(search_url, json={"query": query}, headers=auth_headers)

    # 4. Assert the results
    assert search_response.status_code == 200
    results = search_response.json()

    assert isinstance(results, list)
    assert len(results) > 0

    # The first result should be our uploaded text
    top_result = results[0]
    assert top_result["text"] == file_content
    assert "score" in top_result
    assert top_result["data_source_id"] == upload_response.json()["id"] 