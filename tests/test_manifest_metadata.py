"""Regression tests for the catalog-facing module manifest."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_manifest_state_matches_documented_project_store():
    manifest = json.loads(
        (ROOT / "ellmos-module.v2.json").read_text(encoding="utf-8")
    )
    source = manifest["source_of_truth"]

    assert manifest["state"] == {"ownership": "module", "location": "project"}
    assert source["path"] == "."
    # `repository` stand frueher zusaetzlich auf der Wurzelebene; das Manifest-Schema
    # laesst dort keine Zusatzfelder zu. Geprueft wird deshalb die verbliebene, alleinige
    # Quelle statt der Uebereinstimmung zweier Kopien.
    assert source["repository"], "source_of_truth.repository muss gesetzt sein"
    assert "repository" not in manifest, "keine Dublette auf der Wurzelebene"
    assert "<module-dir>/.grounding-seed/" in (ROOT / "README.md").read_text(
        encoding="utf-8"
    )
    assert "<Modulordner>/.grounding-seed/" in (ROOT / "README_de.md").read_text(
        encoding="utf-8"
    )
