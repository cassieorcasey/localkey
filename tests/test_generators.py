import random
from collections.abc import Sequence

import pytest

from localkey import entropy
from localkey.generators import (
    AMBIGUOUS,
    DIGITS,
    LOWERCASE,
    SYMBOLS,
    UPPERCASE,
    Result,
    random_password,
)


def seeded(seed: int = 42) -> random.Random:
    return random.Random(seed)  # hanya untuk tes, bukan CSPRNG


def test_length_and_charset() -> None:
    result = random_password(32, rng=seeded())
    assert len(result.value) == 32
    assert set(result.value) <= set(LOWERCASE + UPPERCASE + DIGITS + SYMBOLS)


def test_each_class_present_over_many_runs() -> None:
    rng = seeded()
    for _ in range(500):
        value = random_password(4, rng=rng).value
        assert any(c in LOWERCASE for c in value)
        assert any(c in UPPERCASE for c in value)
        assert any(c in DIGITS for c in value)
        assert any(c in SYMBOLS for c in value)


def test_deterministic_with_same_seed() -> None:
    a = random_password(20, rng=seeded(7)).value
    b = random_password(20, rng=seeded(7)).value
    assert a == b


def test_disabled_classes_never_appear() -> None:
    result = random_password(50, symbols=False, uppercase=False, rng=seeded())
    assert set(result.value) <= set(LOWERCASE + DIGITS)


def test_entropy_matches_formula() -> None:
    with_rule = random_password(20, rng=seeded())
    assert with_rule.entropy_bits == pytest.approx(
        entropy.rule_constrained_entropy([26, 26, 10, 32], 20)
    )
    without_rule = random_password(20, require_each=False, rng=seeded())
    assert without_rule.entropy_bits == pytest.approx(entropy.charset_entropy(94, 20))


def test_default_rng_is_used_without_seed() -> None:
    values = {random_password(20).value for _ in range(20)}
    assert len(values) == 20


@pytest.mark.parametrize(
    "kwargs",
    [
        {"length": 0},
        {"length": 3},  # 4 kelas wajib, panjang 3 mustahil
        {
            "lowercase": False,
            "uppercase": False,
            "digits": False,
            "symbols": False,
        },
    ],
)
def test_invalid_arguments(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        random_password(**kwargs)  # type: ignore[arg-type]


def test_max_attempts_exhausted() -> None:
    class AlwaysA:
        def choice(self, seq: Sequence[str]) -> str:
            return "a"

    with pytest.raises(RuntimeError):
        random_password(10, rng=AlwaysA(), max_attempts=5)


def test_repr_hides_password() -> None:
    result = Result("rahasia123", 60.0)
    assert "rahasia123" not in repr(result)
    assert result.strength == "cukup"


def test_exclude_ambiguous_never_emits_ambiguous_chars() -> None:
    rng = seeded()
    for _ in range(300):
        value = random_password(30, exclude_ambiguous=True, rng=rng).value
        assert not set(value) & AMBIGUOUS


def test_exclude_ambiguous_entropy_uses_reduced_class_sizes() -> None:
    # 26-2 (o, l), 26-2 (O, I), 10-2 (0, 1), 32-1 (|)
    result = random_password(20, exclude_ambiguous=True, rng=seeded())
    assert result.entropy_bits == pytest.approx(
        entropy.rule_constrained_entropy([24, 24, 8, 31], 20)
    )
    full = random_password(20, rng=seeded())
    assert result.entropy_bits < full.entropy_bits
