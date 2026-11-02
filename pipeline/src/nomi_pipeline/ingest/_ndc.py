def normalize_ndc(raw: str) -> str:
    segments = raw.split("-")
    if len(segments) != 3 or not all(s.isdigit() for s in segments):
        raise ValueError(f"not a valid NDC: {raw!r}")

    widths = (5, 4, 2)
    for segment, width in zip(segments, widths, strict=True):
        if len(segment) > width:
            raise ValueError(f"not a valid NDC: {raw!r}")
    labeler, product, package = segments
    return labeler.zfill(5) + product.zfill(4) + package.zfill(2)
