import pytest

from grounding_seed.self_knowledge import (
    Need,
    NeedStatus,
    assess,
    status_from_resolution,
)


class _FakeResult:
    """Ein `ResolutionResult`-Double, wie `source_resolver.resolve()` es liefert."""

    def __init__(self, status, quelle=None, nachricht=""):
        self.status = status
        self.quelle = quelle
        self.nachricht = nachricht


class _FakeAssessment:
    """Ein Resolver-Rueckgabewert im assess()-Vertrag: `.status` ist bereits
    found/empty/unavailable -- kein ResolutionStatus mehr."""

    def __init__(self, status, quelle=None, nachricht=""):
        self.status = status
        self.quelle = quelle
        self.nachricht = nachricht


# --- assess(): Vertrag seit 0.2.0 -- Resolver liefert den fertigen Status ---

def test_resolver_reporting_found_is_passed_through():
    report = assess(
        [Need("decisions.ledger")],
        resolver=lambda r: _FakeAssessment(NeedStatus.FOUND, {"x": 1}),
    )
    assert report.assessments[0].status == NeedStatus.FOUND
    assert report.assessments[0].quelle == {"x": 1}


def test_resolver_reporting_empty_is_passed_through():
    """EMPTY kann nur der Aufrufer wissen (er hat den Inhalt gelesen) --
    assess() darf es nicht selbst aus einer Verortung ableiten."""
    report = assess(
        [Need("decisions.ledger")],
        resolver=lambda r: _FakeAssessment(NeedStatus.EMPTY, nachricht="befragt, nichts Neues"),
    )
    assert report.assessments[0].status == NeedStatus.EMPTY


def test_resolver_reporting_unavailable_is_passed_through():
    report = assess(
        [Need("policy.registry")],
        resolver=lambda r: _FakeAssessment(NeedStatus.UNAVAILABLE),
    )
    assert report.assessments[0].status == NeedStatus.UNAVAILABLE


def test_resolver_exception_maps_to_unavailable_not_crash():
    def _boom(rolle):
        raise RuntimeError("Quelle nicht erreichbar")

    report = assess([Need("decisions.ledger")], resolver=_boom)
    assert report.assessments[0].status == NeedStatus.UNAVAILABLE


def test_invalid_status_raises_instead_of_silent_bucketing():
    """Regressionsanker fuer den Kernfehler von 0.1.0: `not_found` (ein roher
    ResolutionStatus, kein NeedStatus) darf NICHT still zu 'empty' oder
    'unavailable' gebogen werden -- assess() muss den Vertragsbruch melden."""
    with pytest.raises(ValueError, match="not_found"):
        assess([Need("decisions.ledger")], resolver=lambda r: _FakeResult("not_found"))


def test_invalid_status_raises_for_raw_resolved_too():
    """Auch ein roher 'resolved' (statt NeedStatus.FOUND) ist ein Vertragsbruch --
    der Aufrufer muss status_from_resolution() nutzen, nicht raten lassen."""
    with pytest.raises(ValueError, match="resolved"):
        assess([Need("decisions.ledger")], resolver=lambda r: _FakeResult("resolved"))


def test_all_answerable_true_when_no_unavailable():
    report = assess(
        [Need("a"), Need("b")],
        resolver=lambda r: _FakeAssessment(NeedStatus.EMPTY) if r == "a" else _FakeAssessment(NeedStatus.FOUND),
    )
    assert report.all_answerable() is True


def test_all_answerable_false_when_any_unavailable():
    report = assess(
        [Need("a"), Need("b")],
        resolver=lambda r: _FakeAssessment(NeedStatus.EMPTY) if r == "a" else _FakeAssessment(NeedStatus.UNAVAILABLE),
    )
    assert report.all_answerable() is False
    assert report.unavailable_roles() == ["b"]


# --- status_from_resolution(): die benannte, korrekte Uebersetzung ---
# resolve() beantwortet nur WO, nie WAS -- darum liefert diese Funktion NIE 'empty'.

def test_status_from_resolution_resolved_is_found():
    assert status_from_resolution(_FakeResult("resolved")) == NeedStatus.FOUND


def test_status_from_resolution_proposed_is_found():
    assert status_from_resolution(_FakeResult("proposed")) == NeedStatus.FOUND


def test_status_from_resolution_not_found_is_unavailable_not_empty():
    """Der Kern der Korrektur: 'keine Rolle verortet' heisst 'ich weiss nicht,
    wohin ich fragen soll' -- das ist unavailable, nie ein geprueftes Leer."""
    assert status_from_resolution(_FakeResult("not_found")) == NeedStatus.UNAVAILABLE


def test_status_from_resolution_module_present_not_callable_is_unavailable():
    assert status_from_resolution(_FakeResult("module_present_not_callable")) == NeedStatus.UNAVAILABLE


def test_status_from_resolution_adapter_error_is_unavailable():
    assert status_from_resolution(_FakeResult("adapter_error")) == NeedStatus.UNAVAILABLE


def test_status_from_resolution_unknown_status_is_unavailable():
    assert status_from_resolution(_FakeResult("something_new")) == NeedStatus.UNAVAILABLE


def test_status_from_resolution_never_returns_empty():
    """Fuer keinen denkbaren ResolutionStatus darf EMPTY herauskommen --
    das waere wieder der urspruengliche Fehler."""
    for raw_status in ("resolved", "proposed", "not_found", "module_present_not_callable",
                        "adapter_error", "no_foreign_providers", None, "anything"):
        assert status_from_resolution(_FakeResult(raw_status)) != NeedStatus.EMPTY


def test_status_from_resolution_used_as_resolver_wrapper_end_to_end():
    """Integrationsmuster: ein Aufrufer, der nur Verortung braucht (keinen
    Inhalt liest), wrappt source_resolver.resolve() so."""

    def location_only_resolver(rolle: str):
        raw = _FakeResult("resolved") if rolle == "user.model" else _FakeResult("not_found")
        return _FakeAssessment(status_from_resolution(raw), quelle=getattr(raw, "quelle", None))

    report = assess(
        [Need("user.model"), Need("memory.curated")],
        resolver=location_only_resolver,
    )
    assert report.by_status(NeedStatus.FOUND)[0].rolle == "user.model"
    assert report.by_status(NeedStatus.UNAVAILABLE)[0].rolle == "memory.curated"
    assert report.all_answerable() is False
