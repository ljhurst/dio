from __future__ import annotations

import pytest
from pydantic import ValidationError

from dio.models import ExtractionRequest, ImageInput, VisionExtraction


def test_extraction_request_accepts_one_to_four_images() -> None:
    images = [ImageInput(data="AA==", media_type="image/jpeg")]
    request = ExtractionRequest(images=images)
    assert len(request.images) == 1


def test_extraction_request_rejects_zero_images() -> None:
    with pytest.raises(ValidationError):
        ExtractionRequest(images=[])


def test_extraction_request_rejects_more_than_four_images() -> None:
    images = [ImageInput(data="AA==", media_type="image/jpeg") for _ in range(5)]
    with pytest.raises(ValidationError):
        ExtractionRequest(images=images)


def test_image_input_rejects_unknown_media_type() -> None:
    with pytest.raises(ValidationError):
        ImageInput(data="AA==", media_type="image/heic")  # type: ignore[arg-type]


def test_vision_extraction_defaults_to_nulls_and_empty_lists() -> None:
    extraction = VisionExtraction()
    assert extraction.producer is None
    assert extraction.vintage is None
    assert extraction.grape_varieties == []
    assert extraction.certifications == []
