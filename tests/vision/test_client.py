from collections.abc import Callable

import anthropic
import pytest

from dio.errors import VisionExtractionError
from dio.models import ExtractionRequest
from dio.vision.client import extract_label
from tests.conftest import FakeMessage, FakeTextBlock

MODEL = "claude-haiku-4-5"


def test_extract_label_parses_valid_json_response(
    make_fake_client: Callable[..., anthropic.Anthropic],
    valid_request: ExtractionRequest,
) -> None:
    payload = (
        '{"producer": "Domaine Example", "wine_name": "Cuvee X", "vintage": 2020, '
        '"country_iso_alpha_3": "FRA", "region": "Burgundy", "appellation": null, '
        '"grape_varieties": ["Pinot Noir"], "abv_percent": 13.5, "volume_ml": 750, '
        '"wine_type": "red", "classification": null, "closure": "cork", '
        '"certifications": [], "barcode": null}'
    )
    client = make_fake_client(
        lambda **_: FakeMessage(content=[FakeTextBlock(text=payload)])
    )

    extraction = extract_label(client, valid_request, MODEL)

    assert extraction.producer == "Domaine Example"
    assert extraction.vintage == 2020
    assert extraction.grape_varieties == ["Pinot Noir"]


def test_extract_label_raises_on_refusal(
    make_fake_client: Callable[..., anthropic.Anthropic],
    valid_request: ExtractionRequest,
) -> None:
    client = make_fake_client(
        lambda **_: FakeMessage(content=[], stop_reason="refusal"),
    )

    with pytest.raises(VisionExtractionError):
        extract_label(client, valid_request, MODEL)


def test_extract_label_raises_on_invalid_json(
    make_fake_client: Callable[..., anthropic.Anthropic],
    valid_request: ExtractionRequest,
) -> None:
    client = make_fake_client(
        lambda **_: FakeMessage(content=[FakeTextBlock(text="not json")]),
    )

    with pytest.raises(VisionExtractionError):
        extract_label(client, valid_request, MODEL)
