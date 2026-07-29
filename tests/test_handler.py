from __future__ import annotations

import base64
import json
from collections.abc import Callable

import anthropic

from dio.enrichment import Enricher
from dio.errors import VisionExtractionError
from dio.handler import handle_event
from dio.models import EnrichmentResult, VisionExtraction
from tests.conftest import VALID_BASE64_JPEG, FakeMessage, FakeTextBlock

MODEL = "claude-haiku-4-5"

VALID_EXTRACTION_JSON = (
    '{"producer": "Domaine Example", "wine_name": "Cuvee X", "vintage": 2020, '
    '"country_iso_alpha_3": "FRA", "region": "Burgundy", "appellation": null, '
    '"grape_varieties": ["Pinot Noir"], "abv_percent": 13.5, "volume_ml": 750, '
    '"wine_type": "red", "classification": null, "closure": "cork", '
    '"certifications": [], "barcode": null}'
)


def _event(
    body: dict[str, object], *, base64_encode: bool = False
) -> dict[str, object]:
    raw = json.dumps(body)
    if base64_encode:
        return {
            "body": base64.b64encode(raw.encode()).decode(),
            "isBase64Encoded": True,
        }
    return {"body": raw, "isBase64Encoded": False}


def _matching_enricher(_: VisionExtraction) -> EnrichmentResult | None:
    return EnrichmentResult(matched=True)


def _failing_enricher(_: VisionExtraction) -> EnrichmentResult | None:
    raise RuntimeError("boom")


def test_handle_event_returns_200_with_label_and_enrichment(
    make_fake_client: Callable[..., anthropic.Anthropic],
) -> None:
    client = make_fake_client(
        lambda **_: FakeMessage(content=[FakeTextBlock(text=VALID_EXTRACTION_JSON)])
    )
    event = _event(
        {"images": [{"data": VALID_BASE64_JPEG, "media_type": "image/jpeg"}]}
    )

    response = handle_event(
        event, client=client, enricher=_matching_enricher, model=MODEL
    )

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["label"]["producer"] == "Domaine Example"
    assert body["enrichment"]["matched"] is True
    assert body["meta"]["warnings"] == []


def test_handle_event_decodes_base64_encoded_body(
    make_fake_client: Callable[..., anthropic.Anthropic],
) -> None:
    client = make_fake_client(
        lambda **_: FakeMessage(content=[FakeTextBlock(text=VALID_EXTRACTION_JSON)])
    )
    event = _event(
        {"images": [{"data": VALID_BASE64_JPEG, "media_type": "image/jpeg"}]},
        base64_encode=True,
    )

    response = handle_event(
        event, client=client, enricher=_matching_enricher, model=MODEL
    )

    assert response["statusCode"] == 200


def test_handle_event_returns_400_on_malformed_body(
    make_fake_client: Callable[..., anthropic.Anthropic],
) -> None:
    client = make_fake_client(lambda **_: FakeMessage(content=[]))
    event = {"body": "not json", "isBase64Encoded": False}

    response = handle_event(
        event, client=client, enricher=_matching_enricher, model=MODEL
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"] == "invalid_request"


def test_handle_event_returns_400_on_invalid_image(
    make_fake_client: Callable[..., anthropic.Anthropic],
) -> None:
    client = make_fake_client(lambda **_: FakeMessage(content=[]))
    event = _event(
        {"images": [{"data": "!!!not-base64!!!", "media_type": "image/jpeg"}]}
    )

    response = handle_event(
        event, client=client, enricher=_matching_enricher, model=MODEL
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"] == "invalid_image"


def test_handle_event_returns_502_on_vision_failure(
    make_fake_client: Callable[..., anthropic.Anthropic],
) -> None:
    def _raise(**_: object) -> FakeMessage:
        raise VisionExtractionError("model unavailable")

    client = make_fake_client(_raise)
    event = _event(
        {"images": [{"data": VALID_BASE64_JPEG, "media_type": "image/jpeg"}]}
    )

    response = handle_event(
        event, client=client, enricher=_matching_enricher, model=MODEL
    )

    assert response["statusCode"] == 502
    assert json.loads(response["body"])["error"] == "vision_extraction_failed"


def test_handle_event_succeeds_with_warning_when_enrichment_fails(
    make_fake_client: Callable[..., anthropic.Anthropic],
) -> None:
    client = make_fake_client(
        lambda **_: FakeMessage(content=[FakeTextBlock(text=VALID_EXTRACTION_JSON)])
    )
    event = _event(
        {"images": [{"data": VALID_BASE64_JPEG, "media_type": "image/jpeg"}]}
    )
    enricher: Enricher = _failing_enricher

    response = handle_event(event, client=client, enricher=enricher, model=MODEL)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["enrichment"] is None
    assert body["meta"]["warnings"] == ["enrichment_failed"]
