import base64

import pytest

from dio.errors import InvalidImageError
from dio.models import ImageInput
from dio.utils.images import MAX_IMAGE_BYTES, decode_images


def test_decode_images_returns_decoded_bytes_in_order() -> None:
    first = base64.b64encode(b"first-image-bytes").decode()
    second = base64.b64encode(b"second-image-bytes").decode()
    images = [
        ImageInput(data=first, media_type="image/jpeg"),
        ImageInput(data=second, media_type="image/png"),
    ]

    decoded = decode_images(images)

    assert decoded == [b"first-image-bytes", b"second-image-bytes"]


def test_decode_images_rejects_invalid_base64() -> None:
    images = [ImageInput(data="not valid base64!!", media_type="image/jpeg")]

    with pytest.raises(InvalidImageError):
        decode_images(images)


def test_decode_images_rejects_oversized_image() -> None:
    oversized = base64.b64encode(b"x" * (MAX_IMAGE_BYTES + 1)).decode()
    images = [ImageInput(data=oversized, media_type="image/jpeg")]

    with pytest.raises(InvalidImageError):
        decode_images(images)
