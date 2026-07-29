from __future__ import annotations

from dio.enrichment import stub_enrich
from dio.models import VisionExtraction


def test_stub_enrich_never_matches() -> None:
    label = VisionExtraction(producer="Domaine Example", vintage=2020)

    result = stub_enrich(label)

    assert result is not None
    assert result.matched is False
    assert result.price is None
    assert result.critic_score is None
