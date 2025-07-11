"""
API endpoints for semantic search.
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import get_current_active_user
from backend.models.user import User
from backend.services.project_service import ProjectService
from backend.services.data_source_service import DataSourceService
from backend.semantic_processing.embedding_service import EmbeddingService

router = APIRouter()
logger = logging.getLogger("api")

class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    text: str
    score: float
    data_source_id: int

@router.post(
    "/projects/{project_id}/search",
    response_model=List[SearchResult],
    summary="Perform semantic search within a project",
    description="Searches for text chunks within a project that are semantically similar to the query.",
)
async def semantic_search(
    project_id: int,
    query: SearchQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Performs semantic search on documents within a specific project.
    """
    # 1. Validate user has access to the project
    project = await ProjectService.get_project_by_id(db, project_id, current_user)
    
    # 2. Get all data source IDs for this project
    project_data_sources = await DataSourceService.get_data_sources_by_project(db, project.id)
    if not project_data_sources:
        return []
    project_ds_ids = [ds.id for ds in project_data_sources]

    # 3. Perform the search using the service
    try:
        search_results = EmbeddingService.search_similar_chunks(
            project_id=project_id,
            query_text=query.query,
            data_source_ids=project_ds_ids
        )
        return search_results
    except Exception as e:
        logger.error(f"Semantic search failed for project {project_id} with query '{query.query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the search."
        ) 