import base64
from pathlib import Path

from dio.models import ImageInput, ImageMediaType, VisionExtraction
from evals.models import EvalCase

IMAGE_MEDIA_TYPES: dict[str, ImageMediaType] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def load_cases(cases_dir: Path) -> list[EvalCase]:
    return [
        _load_case(case_dir)
        for case_dir in sorted(cases_dir.iterdir())
        if case_dir.is_dir()
    ]


def load_images(case: EvalCase) -> list[ImageInput]:
    return [_load_image(path) for path in case.image_paths]


def _load_case(case_dir: Path) -> EvalCase:
    expected = VisionExtraction.model_validate_json(
        (case_dir / "expected.json").read_text()
    )
    image_paths = sorted(_image_paths(case_dir / "images"))
    return EvalCase(case_id=case_dir.name, image_paths=image_paths, expected=expected)


def _image_paths(images_dir: Path) -> list[Path]:
    return [
        path
        for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_MEDIA_TYPES
    ]


def _load_image(path: Path) -> ImageInput:
    media_type = IMAGE_MEDIA_TYPES[path.suffix.lower()]
    data = base64.b64encode(path.read_bytes()).decode()
    return ImageInput(data=data, media_type=media_type)
