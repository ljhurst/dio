from pathlib import Path
from typing import Any

from pydantic import BaseModel

from dio.models import VisionExtraction


class EvalCase(BaseModel):
    case_id: str
    image_paths: list[Path]
    expected: VisionExtraction


class FieldResult(BaseModel):
    field: str
    expected: Any
    actual: Any
    matched: bool


class EvalCaseResult(BaseModel):
    case_id: str
    matched: bool
    field_results: list[FieldResult]


class EvalReport(BaseModel):
    case_results: list[EvalCaseResult]
