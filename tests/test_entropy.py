import math
from itertools import product

import pytest

from localkey import entropy


def test_charset_entropy_hand_calculated() -> None:
    # 8 karakter dari 94 ASCII printable: 8 * log2(94) = 52.44
    assert entropy.charset_entropy(94, 8) == pytest.approx(52.44, abs=0.01)


def test_wordlist_entropy_eff_six_words() -> None:
    # EFF large: 7776 = 6^5 kata, 6 kata = 77.55 bit
    assert entropy.wordlist_entropy(7776, 6) == pytest.approx(77.55, abs=0.01)


def test_case_and_permutation_entropy() -> None:
    assert entropy.case_entropy(9) == 9.0
    assert entropy.permutation_entropy(2) == 1.0
    assert entropy.permutation_entropy(3) == pytest.approx(math.log2(6))


@pytest.mark.parametrize("bad", [(0, 5), (10, -1)])
def test_charset_entropy_rejects_invalid(bad: tuple[int, int]) -> None:
    with pytest.raises(ValueError):
        entropy.charset_entropy(*bad)


def _brute_force_valid(classes: list[str], length: int) -> int:
    alphabet = "".join(classes)
    return sum(
        all(any(ch in cls for ch in combo) for cls in classes)
        for combo in product(alphabet, repeat=length)
    )


@pytest.mark.parametrize(
    ("classes", "length"),
    [
        (["ab", "c"], 3),
        (["ab", "cd", "e"], 4),
        (["abc", "12", "#"], 5),
    ],
)
def test_valid_count_matches_brute_force(classes: list[str], length: int) -> None:
    sizes = [len(c) for c in classes]
    assert entropy.valid_count(sizes, length) == _brute_force_valid(classes, length)


def test_valid_count_zero_when_too_short() -> None:
    assert entropy.valid_count([26, 26, 10, 32], 3) == 0
    with pytest.raises(ValueError):
        entropy.rule_constrained_entropy([26, 26, 10, 32], 3)


def test_rule_penalty_is_small_for_long_passwords() -> None:
    sizes = [26, 26, 10, 32]
    free = entropy.charset_entropy(94, 20)
    constrained = entropy.rule_constrained_entropy(sizes, 20)
    assert constrained < free
    assert free - constrained < 0.5
    p = entropy.acceptance_probability(sizes, 20)
    assert constrained == pytest.approx(free + math.log2(p))


@pytest.mark.parametrize(
    ("bits", "label"),
    [(59.9, "lemah"), (60, "cukup"), (79.9, "cukup"), (80, "kuat")],
)
def test_strength_label_thresholds(bits: float, label: str) -> None:
    assert entropy.strength_label(bits) == label
