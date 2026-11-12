"""Generator password. Semua keacakan proyek ini lewat sini."""

from __future__ import annotations

import secrets
import string
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from . import entropy

LOWERCASE = string.ascii_lowercase  # 26
UPPERCASE = string.ascii_uppercase  # 26
DIGITS = string.digits  # 10
SYMBOLS = string.punctuation  # 32


class RandomSource(Protocol):
    """Apa pun yang punya `.choice(seq)`.

    Produksi: secrets.SystemRandom (CSPRNG dari OS).
    Tes: random.Random(seed) agar hasil bisa diulang. Jangan pernah pakai
    random.Random di luar tes.
    """

    def choice(self, seq: Sequence[str]) -> str: ...


_DEFAULT_RNG: RandomSource = secrets.SystemRandom()


@dataclass(frozen=True)
class Result:
    # repr=False: password tidak ikut tercetak bila objek di-print atau di-log.
    value: str = field(repr=False)
    entropy_bits: float

    @property
    def strength(self) -> str:
        return entropy.strength_label(self.entropy_bits)


def random_password(
    length: int = 20,
    *,
    lowercase: bool = True,
    uppercase: bool = True,
    digits: bool = True,
    symbols: bool = True,
    require_each: bool = True,
    rng: RandomSource | None = None,
    max_attempts: int = 10_000,
) -> Result:
    """Password acak penuh.

    Jika `require_each` aktif, password dijamin memuat minimal satu karakter
    dari tiap kelas yang aktif. Caranya rejection sampling: buat kandidat
    acak, buang jika tidak lolos, ulangi. Posisi karakter wajib tetap acak,
    dan entropinya dihitung eksak dari jumlah string yang valid.
    """
    enabled = [
        cls
        for cls, on in (
            (LOWERCASE, lowercase),
            (UPPERCASE, uppercase),
            (DIGITS, digits),
            (SYMBOLS, symbols),
        )
        if on
    ]
    if not enabled:
        raise ValueError("Minimal satu jenis karakter harus aktif.")
    if length < 1:
        raise ValueError("Panjang minimal 1.")
    if require_each and length < len(enabled):
        raise ValueError(
            f"Panjang {length} terlalu pendek untuk {len(enabled)} jenis karakter."
        )

    source = _DEFAULT_RNG if rng is None else rng
    alphabet = "".join(enabled)
    class_sets = [frozenset(cls) for cls in enabled]

    for _ in range(max_attempts):
        candidate = "".join(source.choice(alphabet) for _ in range(length))
        if not require_each or _covers_all(candidate, class_sets):
            break
    else:
        raise RuntimeError("Gagal memenuhi aturan setelah batas percobaan.")

    if require_each:
        bits = entropy.rule_constrained_entropy([len(c) for c in enabled], length)
    else:
        bits = entropy.charset_entropy(len(alphabet), length)
    return Result(candidate, bits)


def _covers_all(candidate: str, class_sets: list[frozenset[str]]) -> bool:
    chars = set(candidate)
    return all(chars & cls for cls in class_sets)
