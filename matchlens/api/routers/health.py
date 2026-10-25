"""
Health router endpoint.
"""

from fastapi import APIRouter
from matchlens.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """
    Returns system health status and API version.
    """
    return HealthResponse(status="ok", version="v1")
