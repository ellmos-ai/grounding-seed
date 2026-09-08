"""Contract tests for PEP 621 metadata, CI workflow, security policy, and repository hygiene."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

import grounding_seed

ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_pep621_compliance():
    """pyproject.toml must declare PEP 621 compliant metadata."""
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml must exist"

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project", {})

    assert project.get("name") == "grounding-seed"
    assert project.get("version") == grounding_seed.__version__
    assert project.get("requires-python") == ">=3.10"
    assert project.get("license") == {"text": "MIT"}
    assert project.get("authors")
    assert project.get("readme") == "README.md"

    # Classifiers
    classifiers = project.get("classifiers", [])
    assert any("License :: OSI Approved :: MIT License" in c for c in classifiers)
    assert any("Programming Language :: Python :: 3" in c for c in classifiers)
    assert any("Operating System :: OS Independent" in c for c in classifiers)

    # URLs
    urls = project.get("urls", {})
    for expected_key in [
        "Homepage",
        "Documentation",
        "Repository",
        "Issues",
        "Changelog",
        "Security",
        "Parent Organization",
        "Umbrella Ecosystem",
    ]:
        assert expected_key in urls, f"Missing project URL: {expected_key}"


def test_version_parity_across_artifacts():
    """Version string must match exactly across all authoritative files."""
    version = grounding_seed.__version__
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Invalid semver: {version}"

    pyproject_data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject_data["project"]["version"] == version

    template_stamp = grounding_seed.template_stamp()
    assert template_stamp == f"grounding-seed@{version}"

    llms_text = (ROOT / "llms.txt").read_text(encoding="utf-8")
    assert version in llms_text, "Version must be documented in llms.txt"


def test_ci_workflow_integrity():
    """CI workflow must exist, define multi-OS matrix and modern actions."""
    ci_file = ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_file.is_file(), ".github/workflows/ci.yml must exist"

    content = ci_file.read_text(encoding="utf-8")
    assert "ubuntu-latest" in content
    assert "windows-latest" in content
    assert "macos-latest" in content
    assert "actions/checkout@v4" in content
    assert "actions/setup-python@v5" in content
    assert "cache: \"pip\"" in content or "cache: 'pip'" in content
    assert "cancel-in-progress: true" in content
    assert "ruff check ." in content
    assert "compileall" in content
    assert "pytest" in content


def test_security_policy_bilingual_and_complete():
    """SECURITY.md must exist, be bilingual and specify SLA and invariants."""
    sec_file = ROOT / "SECURITY.md"
    assert sec_file.is_file(), "SECURITY.md must exist"

    content = sec_file.read_text(encoding="utf-8")
    assert "## English" in content
    assert "## Deutsch" in content
    assert "48 hours" in content or "48-Stunden" in content or "48 Stunden" in content
    assert "5 business days" in content or "5 Werktagen" in content
    assert "security@open-bricks.org" in content
    assert "Local-First" in content
    assert "Non-Elevation" in content or "ohne Sonderrechte" in content
    assert "abwehren" in content


def test_gitignore_hardening_patterns():
    """.gitignore must include sync conflicts, locks, and cache patterns."""
    gi_file = ROOT / ".gitignore"
    assert gi_file.is_file(), ".gitignore must exist"

    content = gi_file.read_text(encoding="utf-8")
    assert "*.sync-conflict-*" in content
    assert "LOCK*.txt" in content
    assert ".pytest_cache" in content
    assert ".ruff_cache" in content


def test_readme_bilingual_navigation_and_links():
    """Both READMEs must link to SECURITY.md, CHANGELOG.md, and llms.txt."""
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    for readme in (readme_en, readme_de):
        assert "SECURITY.md" in readme
        assert "CHANGELOG.md" in readme
        assert "llms.txt" in readme
