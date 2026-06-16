from fastapi import APIRouter
from schemas.v1.health import HealthResponse
from config.settings import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def check_health() -> HealthResponse:
    """
    Check the health of the API.
    """
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT
    )
