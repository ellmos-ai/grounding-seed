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


def test_record_without_state_leaves_existing_state_unchanged(tmp_path):
    """Regression T-20260906-140331395: state=None (Default) heisst 'kein
    Eskalationswunsch' -- ein Update darf den bestehenden state NICHT anfassen."""
    first = record_candidate(tmp_path, ["a", "b"], "erster Beleg")
    assert first.state == "verbinden"
    second = record_candidate(tmp_path, ["a", "b"], "zweiter Beleg")
    assert second.state == "verbinden"
    assert second.times_observed == 2


def test_record_with_explicit_state_escalates_an_existing_open_candidate(tmp_path):
    """Regression T-20260906-140331395 (Opus-Reviewer-Befund beim Merge von PR#2,
    vorbestehend seit 0.3.0): genau die gemeldete Sequenz -- record_candidate()
    ohne state, dann record_candidate() mit state='abwehren' auf dieselbe
    Paarung -- muss den Kandidaten tatsaechlich auf 'abwehren' eskalieren.
    Vorher liess das den state unveraendert auf 'verbinden'."""
    record_candidate(tmp_path, ["a", "b"], "unauffaellig zuerst")
    escalated = record_candidate(tmp_path, ["a", "b"], "jetzt riskant wirkend", state="abwehren")
    assert escalated.state == "abwehren"
    assert escalated.times_observed == 2
    assert escalated.evidence == "jetzt riskant wirkend"
    candidates = list_candidates(tmp_path)
    assert len(candidates) == 1  # weiterhin derselbe Kandidat, nicht dupliziert


def test_record_cannot_re_state_an_already_quarantined_candidate(tmp_path):
    """'abwehren' bleibt terminal auch gegenueber record_candidate() selbst --
    nicht nur gegenueber confirm_candidate()/dismiss_candidate(). Ein erneuter
    EXPLIZITER state-Versuch auf einen bereits quarantaenierten Kandidaten wird
    abgelehnt, unabhaengig vom Zielwert."""
    record_candidate(tmp_path, ["a", "b"], "sofort riskant", state="abwehren")
    with pytest.raises(ValueError):
        record_candidate(tmp_path, ["a", "b"], "spaeter harmlos?", state="verbinden")
    with pytest.raises(ValueError):
        record_candidate(tmp_path, ["a", "b"], "erneut abwehren", state="abwehren")


def test_record_without_state_still_updates_metadata_on_a_quarantined_candidate(tmp_path):
    """Passives Weiterbeobachten (kein expliziter state) ist auf einem
    quarantaenierten Kandidaten weiterhin erlaubt -- nur eine explizite
    state-Aenderung ist gesperrt, nicht die Funktion insgesamt."""
    record_candidate(tmp_path, ["a", "b"], "sofort riskant", state="abwehren")
    observed_again = record_candidate(tmp_path, ["a", "b"], "immer noch da")
    assert observed_again.state == "abwehren"
    assert observed_again.times_observed == 2
    assert observed_again.evidence == "immer noch da"


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
    assert confirmed.confirmed is True
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


def test_dismiss_never_downgrades_an_abwehren_candidate(tmp_path):
    """Regression (Review-Anmerkung PR#1): dismiss_candidate() darf eine
    bestehende 'abwehren'-Einstufung (Quarantaene, T-20260815-109780293) nicht
    stillschweigend zu 'koexistieren' abschwaechen -- 'abwehren' ist terminal."""
    record_candidate(tmp_path, ["fremdes-tool", "unbekannte-quelle"], "riskant wirkende Kombination",
                      state="abwehren")
    with pytest.raises(ValueError):
        dismiss_candidate(tmp_path, ["fremdes-tool", "unbekannte-quelle"], reason="doch harmlos?")

    candidates = list_candidates(tmp_path)
    assert len(candidates) == 1
    assert candidates[0].state == "abwehren"
    assert candidates[0].dismissed is False


def test_confirm_never_confirms_an_abwehren_candidate(tmp_path):
    """Symmetrisch: confirm_candidate() darf eine Quarantaene-Einstufung nicht
    'bestaetigen' -- das waere ein Widerspruch in sich (confirmed + abwehren)."""
    record_candidate(tmp_path, ["fremdes-tool", "unbekannte-quelle"], "riskant wirkende Kombination",
                      state="abwehren")
    with pytest.raises(ValueError):
        confirm_candidate(tmp_path, ["fremdes-tool", "unbekannte-quelle"])

    candidates = list_candidates(tmp_path)
    assert candidates[0].confirmed is False
    assert candidates[0].state == "abwehren"


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
