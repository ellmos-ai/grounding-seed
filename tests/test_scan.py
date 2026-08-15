from grounding_seed.scan import scan, scan_knowledge, scan_resources


def test_scan_knowledge_finds_known_filenames(tmp_path):
    (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
    (tmp_path / "irrelevant.txt").write_text("x", encoding="utf-8")
    found = scan_knowledge(tmp_path)
    assert len(found) == 1
    assert found[0].name == "AGENTS.md"


def test_scan_knowledge_not_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "AGENTS.md").write_text("x", encoding="utf-8")
    found = scan_knowledge(tmp_path)
    assert found == []


def test_scan_resources_reports_found_and_missing():
    found, missing = scan_resources(["python", "this-program-should-never-exist-xyz"])
    assert "python" in found or "this-program-should-never-exist-xyz" in missing
    assert "this-program-should-never-exist-xyz" in missing


def test_scan_combines_knowledge_and_resources(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("x", encoding="utf-8")
    result = scan(tmp_path, resource_programs=["this-program-should-never-exist-xyz"])
    assert len(result.knowledge_found) == 1
    assert "this-program-should-never-exist-xyz" in result.resources_missing
