# Nomi MVP demo

A throwaway prototype for showing the idea end to end: barcode or brand name → real openFDA label → rule extractor (NOMI-031) → placeholder score with the label text behind every point.

```bash
uv sync
uv run python demo/server.py        # http://localhost:8000
```

- Barcodes: NDC-based UPC-A codes (start with `3`) resolve through openFDA. Regular retail UPCs need the product crosswalk (NOMI-025) and show an explanation instead.
- `demo/cache/` holds openFDA responses for the quick-pick products so the demo works offline.
- Camera scanning uses the browser `BarcodeDetector` API (Chrome on Android/desktop, served over HTTPS).
- The scoring in `index.html` is a placeholder for discussion. It is not the reviewed rubric (NOMI-049/051) and is not medical advice.
