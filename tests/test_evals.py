from pathlib import Path

from dio.models import VisionExtraction
from evals.compare import compare_case
from evals.loader import load_cases
from evals.models import EvalCaseResult, FieldResult
from evals.report import build_report, field_accuracy


def test_compare_case_matches_identical_extractions() -> None:
    extraction = VisionExtraction(producer="Domaine Example", vintage=2020)

    results = compare_case(extraction, extraction.model_copy())

    assert all(result.matched for result in results)


def test_compare_case_flags_mismatched_field() -> None:
    expected = VisionExtraction(producer="Domaine Example", vintage=2020)
    actual = VisionExtraction(producer="Domaine Example", vintage=2019)

    results = compare_case(expected, actual)

    mismatches = [result.field for result in results if not result.matched]
    assert mismatches == ["vintage"]


def test_load_cases_reads_expected_json_and_images(tmp_path: Path) -> None:
    case_dir = tmp_path / "example-case"
    images_dir = case_dir / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "front.jpg").write_bytes(b"fake-jpeg-bytes")
    expected = VisionExtraction(producer="Domaine Example", vintage=2020)
    (case_dir / "expected.json").write_text(expected.model_dump_json())

    cases = load_cases(tmp_path)

    assert len(cases) == 1
    assert cases[0].case_id == "example-case"
    assert cases[0].expected == expected
    assert cases[0].image_paths == [images_dir / "front.jpg"]


def test_load_cases_ignores_non_image_files(tmp_path: Path) -> None:
    case_dir = tmp_path / "example-case"
    images_dir = case_dir / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "front.jpg").write_bytes(b"fake-jpeg-bytes")
    (images_dir / ".DS_Store").write_bytes(b"not-an-image")
    expected = VisionExtraction(producer="Domaine Example", vintage=2020)
    (case_dir / "expected.json").write_text(expected.model_dump_json())

    cases = load_cases(tmp_path)

    assert cases[0].image_paths == [images_dir / "front.jpg"]


def test_field_accuracy_aggregates_across_cases() -> None:
    case_results = [
        EvalCaseResult(
            case_id="a",
            matched=False,
            field_results=[
                FieldResult(field="producer", expected="X", actual="X", matched=True),
                FieldResult(field="vintage", expected=2020, actual=2019, matched=False),
            ],
        ),
        EvalCaseResult(
            case_id="b",
            matched=True,
            field_results=[
                FieldResult(field="producer", expected="Y", actual="Y", matched=True),
                FieldResult(field="vintage", expected=2021, actual=2021, matched=True),
            ],
        ),
    ]

    accuracy = field_accuracy(build_report(case_results))

    assert accuracy == {"producer": 1.0, "vintage": 0.5}
