from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_store
from app.schemas import HealthResponse
from app.store import IndexStore

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(store: Annotated[IndexStore, Depends(get_store)]) -> HealthResponse:
    return HealthResponse(status="ok", exams=len(store.exams()))
