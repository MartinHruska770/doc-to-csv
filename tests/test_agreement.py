import math

from agreement import cohen_kappa, fleiss_kappa, _normalize, _percent_agreement


def test_normalize_variants():
    assert _normalize("ano") == 1
    assert _normalize(" NE ") == 0
    assert _normalize("yes") == 1
    assert _normalize("") is None
    assert _normalize("možná") is None


def test_percent_agreement():
    assert _percent_agreement([1, 0, 1], [1, 0, 0]) == 2 / 3


def test_cohen_kappa_known_value():
    # po=0.75, pe=0.5 -> kappa=0.5
    assert cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]) == 0.5


def test_cohen_kappa_perfect():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0


def test_cohen_kappa_all_same_category():
    # oba vždy 'ano' -> dokonalá shoda i přes pe=1
    assert cohen_kappa([1, 1, 1], [1, 1, 1]) == 1.0


def test_fleiss_kappa_perfect():
    cols = [[1, 0, 1, 0], [1, 0, 1, 0], [1, 0, 1, 0]]
    assert fleiss_kappa(cols) == 1.0


def test_fleiss_kappa_runs_on_partial_agreement():
    cols = [[1, 1, 0, 0], [1, 0, 0, 0], [1, 1, 1, 0]]
    k = fleiss_kappa(cols)
    assert -1.0 <= k <= 1.0 and not math.isnan(k)
