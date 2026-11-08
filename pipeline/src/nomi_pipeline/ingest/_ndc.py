def normalize_ndc(raw: str) -> str:
    """Turn a dashed NDC10 (4-4-2, 5-3-2 or 5-4-1) into an NDC11 (5-4-2)."""
    segments = raw.split("-")
    # isascii() rejects other Unicode digits that isdigit() accepts.
    if len(segments) != 3 or not all(s.isascii() and s.isdigit() for s in segments):
        raise ValueError(f"not a valid NDC: {raw!r}")
    if sum(len(s) for s in segments) != 10:
        raise ValueError(f"not a valid NDC: {raw!r}")

    widths = (5, 4, 2)
    for segment, width in zip(segments, widths, strict=True):
        if len(segment) > width:
            raise ValueError(f"not a valid NDC: {raw!r}")
    labeler, product, package = segments
    return labeler.zfill(5) + product.zfill(4) + package.zfill(2)
