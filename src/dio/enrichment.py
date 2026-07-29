from collections.abc import Callable

from dio.models import EnrichmentResult, VisionExtraction

Enricher = Callable[[VisionExtraction], EnrichmentResult | None]


def stub_enrich(label: VisionExtraction) -> EnrichmentResult | None:
    return EnrichmentResult(matched=False)
