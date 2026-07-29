Each subdirectory here is one eval case:

```
cases/
  <case-id>/
    images/
      front.jpg
      back.jpg        # optional — as many photos as the case needs
    expected.json      # hand-verified ground truth, shape = VisionExtraction
```

`<case-id>` is free text (e.g. `domaine-example-2020`) — it's just used as
the label in eval output, not parsed. `expected.json` must be valid JSON
matching `dio.models.VisionExtraction` exactly (same nullable fields, same
enums) — run it through the model once locally if unsure:

```python
from dio.models import VisionExtraction

VisionExtraction.model_validate_json(open("expected.json").read())
```
