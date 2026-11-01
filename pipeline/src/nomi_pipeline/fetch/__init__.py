"""Download raw sources from the R2 mirror into data/raw/ with checksums (NOMI-008)."""

from nomi_pipeline._stage import placeholder_app
from nomi_pipeline.fetch.rxnorm import fetch_rxnorm

app = placeholder_app("fetch")
app.command("rxnorm")(fetch_rxnorm)
