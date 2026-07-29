import base64
import binascii

from dio.errors import InvalidImageError
from dio.models import ImageInput

MAX_IMAGE_BYTES = 5 * 1024 * 1024


def decode_images(images: list[ImageInput]) -> list[bytes]:
    return [_decode_single(image) for image in images]


def _decode_single(image: ImageInput) -> bytes:
    try:
        decoded = base64.b64decode(image.data, validate=True)
    except binascii.Error as exc:
        raise InvalidImageError(f"image data is not valid base64: {exc}") from exc

    if not decoded:
        raise InvalidImageError("image data decoded to zero bytes")

    if len(decoded) > MAX_IMAGE_BYTES:
        raise InvalidImageError(f"image exceeds max size of {MAX_IMAGE_BYTES} bytes")

    return decoded
