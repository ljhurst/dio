import base64
import json
from datetime import UTC, datetime
from typing import Any

import anthropic
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError

from dio.config import get_settings
from dio.enrichment import Enricher, stub_enrich
from dio.errors import DioError
from dio.models import (
    EnrichmentResult,
    ExtractionRequest,
    ExtractionResponse,
    ResponseMeta,
    VisionExtraction,
)
from dio.utils.images import decode_images
from dio.vision.client import extract_label

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    return handle_event(
        event, client=client, enricher=stub_enrich, model=settings.anthropic_model
    )


def handle_event(
    event: dict[str, Any], client: anthropic.Anthropic, enricher: Enricher, model: str
) -> dict[str, Any]:
    try:
        request = _parse_request(event)
    except ValidationError as exc:
        return _error_response(400, "invalid_request", str(exc))

    try:
        decode_images(request.images)
    except DioError as exc:
        return _error_response(400, "invalid_image", str(exc))

    try:
        response = process_extraction_request(
            request, client=client, enricher=enricher, model=model
        )
    except DioError as exc:
        return _error_response(502, "vision_extraction_failed", str(exc))

    return _success_response(response)


def process_extraction_request(
    request: ExtractionRequest,
    client: anthropic.Anthropic,
    enricher: Enricher,
    model: str,
) -> ExtractionResponse:
    label = extract_label(client, request, model)
    enrichment, warnings = _run_enrichment(label, enricher)

    return ExtractionResponse(
        label=label,
        enrichment=enrichment,
        meta=ResponseMeta(
            model=model, extracted_at=datetime.now(UTC), warnings=warnings
        ),
    )


def _run_enrichment(
    label: VisionExtraction, enricher: Enricher
) -> tuple[EnrichmentResult | None, list[str]]:
    try:
        return enricher(label), []
    except Exception:
        logger.exception("enrichment failed")
        return None, ["enrichment_failed"]


def _parse_request(event: dict[str, Any]) -> ExtractionRequest:
    body = event.get("body", "")

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    return ExtractionRequest.model_validate_json(body)


def _success_response(response: ExtractionResponse) -> dict[str, Any]:
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": response.model_dump_json(),
    }


def _error_response(status_code: int, error_code: str, message: str) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({"error": error_code, "message": message}),
    }
