from dio.models import VisionExtraction
from evals.models import FieldResult


def compare_case(
    expected: VisionExtraction, actual: VisionExtraction
) -> list[FieldResult]:
    return [
        _compare_field(expected, actual, field) for field in type(expected).model_fields
    ]


def _compare_field(
    expected: VisionExtraction, actual: VisionExtraction, field: str
) -> FieldResult:
    expected_value = getattr(expected, field)
    actual_value = getattr(actual, field)
    return FieldResult(
        field=field,
        expected=expected_value,
        actual=actual_value,
        matched=expected_value == actual_value,
    )
