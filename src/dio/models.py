from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1

ImageMediaType = Literal["image/jpeg", "image/png", "image/webp", "image/gif"]


class WineType(StrEnum):
    RED = "red"
    WHITE = "white"
    ROSE = "rose"
    SPARKLING = "sparkling"
    DESSERT = "dessert"
    FORTIFIED = "fortified"


class Closure(StrEnum):
    CORK = "cork"
    SCREWCAP = "screwcap"
    OTHER = "other"


class ImageInput(BaseModel):
    data: str = Field(min_length=1)
    media_type: ImageMediaType


class ExtractionRequest(BaseModel):
    images: list[ImageInput] = Field(min_length=1, max_length=4)


class VisionExtraction(BaseModel):
    producer: str | None = None
    wine_name: str | None = None
    vintage: int | None = None
    country_iso_alpha_3: str | None = None
    region: str | None = None
    appellation: str | None = None
    grape_varieties: list[str] = Field(default_factory=list)
    abv_percent: float | None = None
    volume_ml: int | None = None
    wine_type: WineType | None = None
    classification: str | None = None
    closure: Closure | None = None
    certifications: list[str] = Field(default_factory=list)
    barcode: str | None = None


class PriceInfo(BaseModel):
    currency: str
    average: float
    min: float
    max: float


class CriticScore(BaseModel):
    score: float
    scale: float


class EnrichmentResult(BaseModel):
    matched: bool
    wine_searcher_url: str | None = None
    price: PriceInfo | None = None
    critic_score: CriticScore | None = None


class ResponseMeta(BaseModel):
    model: str
    extracted_at: datetime
    warnings: list[str] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    schema_version: int = SCHEMA_VERSION
    label: VisionExtraction
    enrichment: EnrichmentResult | None
    meta: ResponseMeta
