from grounding_seed.self_knowledge import Need, NeedStatus, assess


class _FakeResult:
    def __init__(self, status, quelle=None, nachricht=""):
        self.status = status
        self.quelle = quelle
        self.nachricht = nachricht


def test_resolved_maps_to_found():
    report = assess([Need("decisions.ledger")], resolver=lambda r: _FakeResult("resolved", {"x": 1}))
    assert report.assessments[0].status == NeedStatus.FOUND
    assert report.assessments[0].quelle == {"x": 1}


def test_proposed_maps_to_found():
    report = assess([Need("decisions.ledger")], resolver=lambda r: _FakeResult("proposed"))
    assert report.assessments[0].status == NeedStatus.FOUND


def test_not_found_maps_to_empty():
    report = assess([Need("decisions.ledger")], resolver=lambda r: _FakeResult("not_found"))
    assert report.assessments[0].status == NeedStatus.EMPTY


def test_module_present_not_callable_maps_to_unavailable():
    """Kern des Ticket-Befunds: eine nicht befragbare Quelle ist KEIN 'empty'."""
    report = assess([Need("policy.registry")], resolver=lambda r: _FakeResult("module_present_not_callable"))
    assert report.assessments[0].status == NeedStatus.UNAVAILABLE


def test_adapter_error_maps_to_unavailable():
    report = assess([Need("policy.registry")], resolver=lambda r: _FakeResult("adapter_error"))
    assert report.assessments[0].status == NeedStatus.UNAVAILABLE


def test_resolver_exception_maps_to_unavailable_not_crash():
    def _boom(rolle):
        raise RuntimeError("Quelle nicht erreichbar")

    report = assess([Need("decisions.ledger")], resolver=_boom)
    assert report.assessments[0].status == NeedStatus.UNAVAILABLE


def test_all_answerable_true_when_no_unavailable():
    report = assess(
        [Need("a"), Need("b")],
        resolver=lambda r: _FakeResult("not_found") if r == "a" else _FakeResult("resolved"),
    )
    assert report.all_answerable() is True


def test_all_answerable_false_when_any_unavailable():
    report = assess(
        [Need("a"), Need("b")],
        resolver=lambda r: _FakeResult("not_found") if r == "a" else _FakeResult("module_present_not_callable"),
    )
    assert report.all_answerable() is False
    assert report.unavailable_roles() == ["b"]
