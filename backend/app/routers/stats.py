from typing import Annotated

from fastapi import APIRouter, Depends

from app.constants import Split
from app.dependencies import get_store
from app.schemas import StatsResponse
from app.services.statistics import compute_stats
from app.store import IndexStore

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    store: Annotated[IndexStore, Depends(get_store)],
    split: Split | None = None,
) -> StatsResponse:
    return compute_stats(store.exams(), split)
