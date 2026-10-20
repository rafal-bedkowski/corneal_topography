from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import Settings
from app.constants import MAP_SPEC_BY_TYPE, Label, Laterality, Split
from app.dependencies import get_settings, get_store
from app.models import ExamRecord
from app.schemas import ExamDetail, ExamPage, ExamSummary, MapDetail
from app.services.listing import SortKey, SortOrder, filter_exams, paginate, sort_exams
from app.store import IndexStore

router = APIRouter(prefix="/exams", tags=["exams"])

THUMBNAIL_MAP = "sag_a"


def image_url(exam_id: str, map_type: str) -> str:
    return f"/api/exams/{exam_id}/maps/{map_type}/image"


def to_summary(exam: ExamRecord) -> ExamSummary:
    return ExamSummary(
        exam_id=exam.exam_id,
        split=exam.split,
        label=exam.label,
        case=exam.case,
        laterality=exam.laterality,
        min_thickness_um=exam.indicators.min_thickness_um,
        max_curvature_a_d=exam.indicators.max_curvature_a_d,
        possible_duplicate_of=exam.possible_duplicate_of,
        stats_excluded=exam.stats_excluded,
        thumbnail_url=image_url(exam.exam_id, THUMBNAIL_MAP)
        if THUMBNAIL_MAP in exam.maps
        else None,
    )


def to_detail(exam: ExamRecord) -> ExamDetail:
    return ExamDetail(
        exam_id=exam.exam_id,
        split=exam.split,
        label=exam.label,
        case=exam.case,
        laterality=exam.laterality,
        maps={
            map_type: MapDetail(
                title=MAP_SPEC_BY_TYPE[map_type].title,
                unit=MAP_SPEC_BY_TYPE[map_type].unit,
                image_url=image_url(exam.exam_id, map_type),
                values=record.values,
            )
            for map_type, record in exam.maps.items()
        },
        indicators=exam.indicators,
        possible_duplicate_of=exam.possible_duplicate_of,
        stats_excluded=exam.stats_excluded,
        stats_exclusion_reason=exam.stats_exclusion_reason,
    )


def _find_exam(store: IndexStore, split: str, label: str, case: str) -> ExamRecord:
    exam = store.get(f"{split}/{label}/{case}")
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.get("", response_model=ExamPage)
def list_exams(
    store: Annotated[IndexStore, Depends(get_store)],
    split: Split | None = None,
    label: Label | None = None,
    laterality: Laterality | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
    sort: SortKey = "case",
    order: SortOrder = "asc",
) -> ExamPage:
    matching = filter_exams(store.exams(), split, label, laterality)
    ordered = sort_exams(matching, sort, order)
    return ExamPage(
        total=len(ordered),
        page=page,
        page_size=page_size,
        items=[to_summary(exam) for exam in paginate(ordered, page, page_size)],
    )


@router.get("/{split}/{label}/{case}", response_model=ExamDetail)
def get_exam(
    split: str,
    label: str,
    case: str,
    store: Annotated[IndexStore, Depends(get_store)],
) -> ExamDetail:
    return to_detail(_find_exam(store, split, label, case))


@router.get("/{split}/{label}/{case}/maps/{map_type}/image")
def get_map_image(
    split: str,
    label: str,
    case: str,
    map_type: str,
    store: Annotated[IndexStore, Depends(get_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileResponse:
    exam = _find_exam(store, split, label, case)
    record = next((item for key, item in exam.maps.items() if key == map_type), None)
    if record is None:
        raise HTTPException(status_code=404, detail="Map not found")
    root = settings.dataset_dir.resolve()
    path = (root / record.file).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(Path(path), media_type="image/jpeg")
