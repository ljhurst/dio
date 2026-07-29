import sys
from pathlib import Path

import anthropic

from dio.config import get_settings
from dio.models import ExtractionRequest
from dio.vision.client import extract_label
from evals.compare import compare_case
from evals.loader import load_cases, load_images
from evals.models import EvalCase, EvalCaseResult
from evals.report import build_report, print_report

CASES_DIR = Path(__file__).parent / "cases"


def main() -> None:
    settings = get_settings()

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    cases = load_cases(CASES_DIR)
    case_results = [_run_case(case, client, settings.anthropic_model) for case in cases]

    report = build_report(case_results)
    print_report(report)

    if any(not case_result.matched for case_result in case_results):
        sys.exit(1)


def _run_case(
    case: EvalCase, client: anthropic.Anthropic, model: str
) -> EvalCaseResult:
    request = ExtractionRequest(images=load_images(case))
    actual = extract_label(client, request, model)

    field_results = compare_case(case.expected, actual)

    matched = all(field_result.matched for field_result in field_results)

    return EvalCaseResult(
        case_id=case.case_id, matched=matched, field_results=field_results
    )


if __name__ == "__main__":
    main()
