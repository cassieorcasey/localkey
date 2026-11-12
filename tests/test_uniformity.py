"""Uji chi-square: apakah setiap karakter muncul dengan peluang yang sama?

H0 (hipotesis nol): sumber acak memilih tiap karakter dengan peluang 1/k.
Statistik chi-square mengukur selisih frekuensi teramati dengan frekuensi
harapan (n/k). p-value kecil berarti selisih sebesar itu jarang terjadi
kalau H0 benar, jadi kita curiga ada bias.

Tes bertanda `statistical` memakai keacakan sungguhan, sehingga sesekali
bisa gagal walau tidak ada bias (peluangnya = ALPHA). Karena itu tes tersebut
tidak ikut `pytest` biasa. Jalankan dengan: pytest -m statistical
"""

from __future__ import annotations

import random
import secrets
from collections import Counter
from collections.abc import Iterable

import pytest

from localkey.generators import DIGITS, LOWERCASE, SYMBOLS, UPPERCASE, random_password

stats = pytest.importorskip("scipy.stats")

ALPHABET = LOWERCASE + UPPERCASE + DIGITS + SYMBOLS
N_SAMPLES = 100_000
ALPHA = 0.001


def chi_square_pvalue(samples: Iterable[str], alphabet: str) -> float:
    counts = Counter(samples)
    assert set(counts) <= set(alphabet), "ada karakter di luar alfabet"
    observed = [counts[ch] for ch in alphabet]
    # Tanpa f_exp, scipy menganggap distribusi harapannya seragam.
    return float(stats.chisquare(observed).pvalue)


# Tes deterministik: seed tetap, hasil selalu sama, tidak pernah flaky.


def test_seeded_uniform_source_passes() -> None:
    rng = random.Random(2026)
    samples = (rng.choice(ALPHABET) for _ in range(N_SAMPLES))
    assert chi_square_pvalue(samples, ALPHABET) > ALPHA


def test_biased_source_is_detected() -> None:
    # Bias kecil: 2% pilihan dipaksa jadi "a". Uji harus menangkapnya.
    rng = random.Random(2026)

    def biased_choice() -> str:
        return "a" if rng.random() < 0.02 else rng.choice(ALPHABET)

    samples = (biased_choice() for _ in range(N_SAMPLES))
    assert chi_square_pvalue(samples, ALPHABET) < ALPHA


# Tes statistik: keacakan sungguhan dari OS.


@pytest.mark.statistical
def test_secrets_choice_is_uniform() -> None:
    samples = (secrets.choice(ALPHABET) for _ in range(N_SAMPLES))
    assert chi_square_pvalue(samples, ALPHABET) > ALPHA


@pytest.mark.statistical
def test_random_password_without_rule_is_uniform() -> None:
    # 5.000 password x 20 karakter = 100.000 karakter.
    # require_each=False: lihat EXPLAIN.md, aturan "wajib tiap jenis"
    # sengaja menggeser frekuensi per karakter.
    chars = "".join(
        random_password(20, require_each=False).value for _ in range(N_SAMPLES // 20)
    )
    assert chi_square_pvalue(chars, ALPHABET) > ALPHA
