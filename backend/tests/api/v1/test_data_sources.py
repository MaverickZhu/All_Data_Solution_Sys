import pytest
import httpx
from typing import Any, AsyncGenerator
from io import BytesIO
from PIL import Image
import numpy as np
from pathlib import Path

from backend.main import app
from backend.core.database import get_db
from backend.models.user import User
from backend.models.project import Project
from backend.core.config import settings

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio

async def test_find_similar_images_api(
    async_client: httpx.AsyncClient, 
    auth_headers: dict, 
    test_project: Project,
    tmp_path: Path,
    monkeypatch
):
    """
    Test the full API flow for finding similar images.
    """
    # Override the upload directory for the duration of the test
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    def create_image_file(name: str, modification: int = 0) -> tuple[str, BytesIO]:
        """Helper to create an in-memory image file."""
        array = np.full((10, 10, 3), 128 + modification, dtype=np.uint8) # Grey image
        if modification != 0:
            array[5,5] = (0,0,255) # Add a blue dot for slight modification
        
        img = Image.fromarray(array)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return (name, buffer)

    # 1. Create three images: two similar, one different
    original_img = create_image_file("original.png")
    similar_img = create_image_file("similar.png", modification=5) # Slightly different grey
    
    different_img_array = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
    different_img = Image.fromarray(different_img_array)
    different_buffer = BytesIO()
    different_img.save(different_buffer, format="PNG")
    different_buffer.seek(0)
    different_img_file = ("different.png", different_buffer)

    # 2. Upload images to create data sources
    upload_url = f"/api/v1/data_sources/upload?project_id={test_project.id}"
    
    response_orig = await async_client.post(upload_url, files={"file": original_img}, headers=auth_headers)
    assert response_orig.status_code == 201
    ds_orig_id = response_orig.json()["id"]

    response_sim = await async_client.post(upload_url, files={"file": similar_img}, headers=auth_headers)
    assert response_sim.status_code == 201
    ds_sim_id = response_sim.json()["id"]

    response_diff = await async_client.post(upload_url, files={"file": different_img_file}, headers=auth_headers)
    assert response_diff.status_code == 201
    ds_diff_id = response_diff.json()["id"]

    # 3. Call the similarity endpoint
    # Use a high threshold to ensure the slightly modified image is found
    similar_url = f"/api/v1/data_sources/{ds_orig_id}/similar?project_id={test_project.id}&threshold=10"
    response_search = await async_client.get(similar_url, headers=auth_headers)

    # 4. Assert the results
    assert response_search.status_code == 200
    similar_results = response_search.json()

    assert isinstance(similar_results, list)
    assert len(similar_results) == 1
    
    result_ids = {res["id"] for res in similar_results}
    assert ds_sim_id in result_ids
    assert ds_diff_id not in result_ids

# Test cases will be added below 