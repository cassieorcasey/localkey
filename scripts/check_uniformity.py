"""Cetak hasil uji chi-square untuk sumber acak LocalKey.

Pemakaian:
    python scripts/check_uniformity.py
    python scripts/check_uniformity.py --samples 500000 --exclude-ambiguous
"""

from __future__ import annotations

import argparse
import secrets
from collections import Counter

from scipy.stats import chisquare

from localkey.generators import (
    AMBIGUOUS,
    DIGITS,
    LOWERCASE,
    SYMBOLS,
    UPPERCASE,
    random_password,
)

ALPHA = 0.001
# Aturan praktis chi-square: frekuensi harapan tiap kategori minimal 5.
MIN_EXPECTED = 5
PASSWORD_LENGTH = 20


def report(name: str, samples: str, alphabet: str, note: str = "") -> None:
    counts = Counter(samples)
    observed = [counts[ch] for ch in alphabet]
    result = chisquare(observed)
    expected = len(samples) / len(alphabet)
    rarest = min(alphabet, key=lambda ch: counts[ch])
    commonest = max(alphabet, key=lambda ch: counts[ch])
    print(f"\n{name}")
    print(f"  sampel        : {len(samples):,} karakter, {len(alphabet)} simbol")
    print(f"  harapan/simbol: {expected:,.1f}")
    print(f"  paling jarang : {rarest!r} {counts[rarest]:,}")
    print(f"  paling sering : {commonest!r} {counts[commonest]:,}")
    print(
        f"  chi2 = {result.statistic:.2f}, df = {len(alphabet) - 1}, "
        f"p = {result.pvalue:.3g}"
    )
    verdict = "tidak ada bukti bias" if result.pvalue > ALPHA else "BIAS terdeteksi"
    print(f"  kesimpulan    : {verdict} (alpha = {ALPHA})")
    if note:
        print(f"  catatan       : {note}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=100_000)
    parser.add_argument("--exclude-ambiguous", action="store_true")
    args = parser.parse_args()

    alphabet = LOWERCASE + UPPERCASE + DIGITS + SYMBOLS
    if args.exclude_ambiguous:
        alphabet = "".join(c for c in alphabet if c not in AMBIGUOUS)
    n = args.samples

    min_samples = MIN_EXPECTED * len(alphabet)
    if n < min_samples:
        parser.error(
            f"--samples minimal {min_samples} untuk {len(alphabet)} simbol "
            f"(frekuensi harapan tiap simbol harus >= {MIN_EXPECTED})"
        )

    report(
        "secrets.choice", "".join(secrets.choice(alphabet) for _ in range(n)), alphabet
    )

    def passwords(require_each: bool) -> str:
        return "".join(
            random_password(
                PASSWORD_LENGTH,
                require_each=require_each,
                exclude_ambiguous=args.exclude_ambiguous,
            ).value
            for _ in range(n // PASSWORD_LENGTH)
        )

    report("random_password, require_each=False", passwords(False), alphabet)
    report(
        "random_password, require_each=True",
        passwords(True),
        alphabet,
        note=(
            "hasil ini diharapkan. Aturan situs membuang kandidat tanpa angka, "
            "jadi frekuensi per karakter tidak seragam. Setiap password valid "
            "tetap sama peluangnya (lihat EXPLAIN.md)."
        ),
    )


if __name__ == "__main__":
    main()