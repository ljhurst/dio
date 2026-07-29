from __future__ import annotations

import base64
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

import anthropic
import pytest

from dio.models import ExtractionRequest, ImageInput

VALID_BASE64_JPEG = base64.b64encode(b"not-a-real-jpeg-but-nonempty-bytes").decode()


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeMessage:
    content: list[FakeTextBlock]
    stop_reason: str = "end_turn"


@dataclass
class FakeMessages:
    responder: Callable[..., FakeMessage]

    def create(self, **kwargs: Any) -> FakeMessage:
        return self.responder(**kwargs)


@dataclass
class FakeAnthropicClient:
    responder: Callable[..., FakeMessage]
    messages: FakeMessages = field(init=False)

    def __post_init__(self) -> None:
        self.messages = FakeMessages(self.responder)


@pytest.fixture
def make_fake_client() -> Callable[[Callable[..., FakeMessage]], anthropic.Anthropic]:
    def _make(responder: Callable[..., FakeMessage]) -> anthropic.Anthropic:
        return cast(anthropic.Anthropic, FakeAnthropicClient(responder))

    return _make


@pytest.fixture
def valid_request() -> ExtractionRequest:
    return ExtractionRequest(
        images=[ImageInput(data=VALID_BASE64_JPEG, media_type="image/jpeg")]
    )
