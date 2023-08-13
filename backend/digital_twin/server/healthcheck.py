from fastapi import APIRouter

from digital_twin.server.model import StatusResponse

router = APIRouter()


@router.get("/health", response_model=StatusResponse)
def healthcheck() -> StatusResponse:
    return StatusResponse(success=True, message="ok")
