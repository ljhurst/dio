from typing import Any, cast

import anthropic
from anthropic.types import MessageParam

from dio.errors import VisionExtractionError
from dio.models import ExtractionRequest, VisionExtraction

from .prompts import SYSTEM_PROMPT, USER_PROMPT

MAX_TOKENS = 2048

VISION_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "producer": {"type": ["string", "null"]},
        "wine_name": {"type": ["string", "null"]},
        "vintage": {"type": ["integer", "null"]},
        "country_iso_alpha_3": {"type": ["string", "null"]},
        "region": {"type": ["string", "null"]},
        "appellation": {"type": ["string", "null"]},
        "grape_varieties": {"type": "array", "items": {"type": "string"}},
        "abv_percent": {"type": ["number", "null"]},
        "volume_ml": {"type": ["integer", "null"]},
        "wine_type": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": [
                        "red",
                        "white",
                        "rose",
                        "sparkling",
                        "dessert",
                        "fortified",
                    ],
                },
                {"type": "null"},
            ]
        },
        "classification": {"type": ["string", "null"]},
        "closure": {
            "anyOf": [
                {"type": "string", "enum": ["cork", "screwcap", "other"]},
                {"type": "null"},
            ]
        },
        "certifications": {"type": "array", "items": {"type": "string"}},
        "barcode": {"type": ["string", "null"]},
    },
    "required": [
        "producer",
        "wine_name",
        "vintage",
        "country_iso_alpha_3",
        "region",
        "appellation",
        "grape_varieties",
        "abv_percent",
        "volume_ml",
        "wine_type",
        "classification",
        "closure",
        "certifications",
        "barcode",
    ],
    "additionalProperties": False,
}


def extract_label(
    client: anthropic.Anthropic, request: ExtractionRequest, model: str
) -> VisionExtraction:
    response = client.messages.create(
        model=model,
        temperature=0,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        output_config={
            "format": {"type": "json_schema", "schema": VISION_EXTRACTION_SCHEMA},
        },
        messages=[_build_user_message(request)],
    )
    return _parse_extraction(response)


def _build_user_message(request: ExtractionRequest) -> MessageParam:
    content: list[dict[str, Any]] = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": image.media_type,
                "data": image.data,
            },
        }
        for image in request.images
    ]
    content.append({"type": "text", "text": USER_PROMPT})
    return cast(MessageParam, {"role": "user", "content": content})


def _parse_extraction(response: anthropic.types.Message) -> VisionExtraction:
    if response.stop_reason == "refusal":
        raise VisionExtractionError("vision model refused the request")

    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise VisionExtractionError("vision model returned no text content")

    try:
        return VisionExtraction.model_validate_json(text_blocks[0])
    except ValueError as exc:
        raise VisionExtractionError(
            f"vision model output failed validation: {exc}"
        ) from exc
