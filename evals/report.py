from evals.models import EvalCaseResult, EvalReport


def build_report(case_results: list[EvalCaseResult]) -> EvalReport:
    return EvalReport(case_results=case_results)


def print_report(report: EvalReport) -> None:
    for case_result in report.case_results:
        status = "PASS" if case_result.matched else "FAIL"
        print(f"[{status}] {case_result.case_id}")
        for field_result in case_result.field_results:
            if not field_result.matched:
                print(
                    f"    {field_result.field}: expected={field_result.expected!r} "
                    f"actual={field_result.actual!r}"
                )

    print()
    print(f"{_count_matched(report)}/{len(report.case_results)} cases passed")
    for field, accuracy in field_accuracy(report).items():
        print(f"  {field}: {accuracy:.0%}")


def field_accuracy(report: EvalReport) -> dict[str, float]:
    totals: dict[str, int] = {}
    matches: dict[str, int] = {}
    for case_result in report.case_results:
        for field_result in case_result.field_results:
            totals[field_result.field] = totals.get(field_result.field, 0) + 1
            if field_result.matched:
                matches[field_result.field] = matches.get(field_result.field, 0) + 1
    return {field: matches.get(field, 0) / total for field, total in totals.items()}


def _count_matched(report: EvalReport) -> int:
    return sum(1 for case_result in report.case_results if case_result.matched)
