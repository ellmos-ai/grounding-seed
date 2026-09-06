import pytest

from grounding_seed.fertilizer import (
    confirm_candidate,
    dismiss_candidate,
    list_candidates,
    record_candidate,
)


def test_record_requires_at_least_two_components(tmp_path):
    with pytest.raises(ValueError):
        record_candidate(tmp_path, ["usmc"], "nutze usmc")


def test_record_rejects_unknown_link_type_and_state(tmp_path):
    with pytest.raises(ValueError):
        record_candidate(tmp_path, ["usmc", "policies"], "x", link_type="wurmloch")
    with pytest.raises(ValueError):
        record_candidate(tmp_path, ["usmc", "policies"], "x", state="ignorieren")


def test_record_creates_candidate_at_stufe_2_proposed(tmp_path):
    candidate = record_candidate(
        tmp_path, ["usmc", "policies"], "nutze usmc und mache das und das und policies",
    )
    assert candidate.stufe == 2  # Stufe.DISCOVERY_VORSCHLAG -- konservativer Default
    assert candidate.status == "proposed"
    assert candidate.herkunft == "organic-growth"
    assert candidate.confirmed is False
    assert candidate.times_observed == 1


def test_record_is_order_independent_and_case_insensitive(tmp_path):
    record_candidate(tmp_path, ["USMC", "Policies"], "erster Beleg")
    second = record_candidate(tmp_path, ["policies", "usmc"], "zweiter Beleg")
    candidates = list_candidates(tmp_path)
    assert len(candidates) == 1  # dieselbe Kookkurrenz, nicht dupliziert
    assert second.times_observed == 2
    assert second.evidence == "zweiter Beleg"


def test_record_does_not_update_confirmed_candidate(tmp_path):
    record_candidate(tmp_path, ["usmc", "policies"], "erster Beleg")
    confirm_candidate(tmp_path, ["usmc", "policies"])
    # Neue Beobachtung derselben Paarung nach Bestaetigung -> eigener neuer Kandidat,
    # der bestaetigte bleibt unangetastet (kein stilles Ueberschreiben einer Bestaetigung).
    record_candidate(tmp_path, ["usmc", "policies"], "neuer Beleg")
    candidates = list_candidates(tmp_path)
    assert len(candidates) == 2
    confirmed = [c for c in candidates if c.confirmed]
    assert len(confirmed) == 1
    assert confirmed[0].evidence == "erster Beleg"


def test_confirm_sets_metadata_without_promoting_stufe(tmp_path):
    record_candidate(tmp_path, ["usmc", "policies"], "beleg")
    confirmed = confirm_candidate(tmp_path, ["policies", "usmc"], bestaetigt_von="lukas")
    assert confirmed.confirmed is True
    assert confirmed.confirmed_von == "lukas"
    assert confirmed.confirmed_at
    assert confirmed.stufe == 2  # bleibt Stufe 2 -- kein automatischer Aufstieg


def test_confirm_unknown_candidate_raises(tmp_path):
    with pytest.raises(ValueError):
        confirm_candidate(tmp_path, ["a", "b"])


def test_confirm_targets_the_open_candidate_not_an_older_confirmed_one(tmp_path):
    """Regression: nach einer Bestaetigung kann record_candidate() fuer dieselbe
    Paarung einen zweiten, neuen offenen Kandidaten anlegen. confirm_candidate()
    muss DIESEN treffen -- nicht den ersten Treffer nach Key, der der bereits
    bestaetigte Alteintrag waere."""
    record_candidate(tmp_path, ["usmc", "policies"], "erster Beleg")
    confirm_candidate(tmp_path, ["usmc", "policies"])
    record_candidate(tmp_path, ["usmc", "policies"], "zweiter Beleg")

    newly_confirmed = confirm_candidate(tmp_path, ["usmc", "policies"], bestaetigt_von="lukas")
    assert newly_confirmed.evidence == "zweiter Beleg"

    candidates = list_candidates(tmp_path)
    assert len(candidates) == 2
    assert all(c.confirmed for c in candidates)

    # Ein dritter Aufruf findet keinen offenen Kandidaten mehr -- kein stilles
    # Re-Bestaetigen eines Alteintrags.
    with pytest.raises(ValueError):
        confirm_candidate(tmp_path, ["usmc", "policies"])


def test_dismiss_never_touches_an_already_confirmed_candidate(tmp_path):
    """Regression: dismiss_candidate() darf niemals einen bereits bestaetigten
    Eintrag treffen -- sonst entstuende confirmed=True UND dismissed=True
    gleichzeitig, ein widerspruechlicher Zustand."""
    record_candidate(tmp_path, ["blender", "ffmpeg"], "erster Beleg")
    confirmed = confirm_candidate(tmp_path, ["blender", "ffmpeg"])
    record_candidate(tmp_path, ["blender", "ffmpeg"], "zweiter Beleg")

    dismissed = dismiss_candidate(tmp_path, ["blender", "ffmpeg"], reason="Zweitbeobachtung war Zufall")
    assert dismissed.evidence == "zweiter Beleg"
    assert dismissed.dismissed is True
    assert dismissed.confirmed is False  # nicht der bestaetigte Alteintrag

    # Der zuerst bestaetigte Eintrag bleibt unangetastet: nicht dismissed.
    candidates = list_candidates(tmp_path, include_dismissed=True)
    still_confirmed = [c for c in candidates if c.evidence == "erster Beleg"][0]
    assert still_confirmed.confirmed is True
    assert still_confirmed.dismissed is False


def test_dismiss_marks_koexistieren_and_persists(tmp_path):
    record_candidate(tmp_path, ["blender", "ffmpeg"], "einmalig erwaehnt")
    dismissed = dismiss_candidate(tmp_path, ["blender", "ffmpeg"], reason="nur einmalig, kein Muster")
    assert dismissed.dismissed is True
    assert dismissed.state == "koexistieren"
    assert dismissed.dismissed_reason == "nur einmalig, kein Muster"
    # list_candidates() blendet Verworfenes standardmaessig aus -- kein erneuter
    # Vorschlag bei jedem Lauf (T-20260815-109780293: 'muss PERSISTIERT werden').
    assert list_candidates(tmp_path) == []
    assert list_candidates(tmp_path, include_dismissed=True) == [dismissed]


def test_list_candidates_can_exclude_confirmed(tmp_path):
    record_candidate(tmp_path, ["a", "b"], "x")
    confirm_candidate(tmp_path, ["a", "b"])
    record_candidate(tmp_path, ["c", "d"], "y")
    open_only = list_candidates(tmp_path, include_confirmed=False)
    assert len(open_only) == 1
    assert set(open_only[0].components) == {"c", "d"}


def test_candidates_persist_across_reads(tmp_path):
    record_candidate(tmp_path, ["a", "b"], "x")
    record_candidate(tmp_path, ["c", "d", "e"], "y")
    candidates = list_candidates(tmp_path)
    assert len(candidates) == 2
    path = tmp_path / "connections-candidates.json"
    assert path.exists()
