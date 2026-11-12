from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from itertools import combinations

MIN_BITS = 60.0
STRONG_BITS = 80.0


def charset_entropy(charset_size: int, length: int) -> float:
    """Entropi `length` karakter yang dipilih seragam dari `charset_size` simbol."""
    if charset_size < 1:
        raise ValueError("charset_size minimal 1")
    if length < 0:
        raise ValueError("length tidak boleh negatif")
    return length * math.log2(charset_size)


def wordlist_entropy(wordlist_size: int, word_count: int) -> float:
    """Entropi `word_count` kata yang dipilih seragam dari daftar `wordlist_size`."""
    return charset_entropy(wordlist_size, word_count)


def case_entropy(letter_count: int) -> float:
    """Huruf besar/kecil acak: 1 bit per huruf alfabet."""
    if letter_count < 0:
        raise ValueError("letter_count tidak boleh negatif")
    return float(letter_count)


def permutation_entropy(item_count: int) -> float:
    """Entropi urutan acak dari `item_count` item: log2(k!)."""
    if item_count < 0:
        raise ValueError("item_count tidak boleh negatif")
    return math.log2(math.factorial(item_count))


def valid_count(class_sizes: Sequence[int], length: int) -> int:
    """Jumlah string sepanjang `length` yang memuat minimal satu karakter
    dari setiap kelas.

    Kelas harus saling lepas (tidak ada karakter yang sama). Dihitung dengan
    prinsip inklusi-eksklusi:

        sum over S subset of kelas: (-1)^|S| * (N - |gabungan S|)^length

    Semua aritmetika integer, jadi hasilnya eksak.
    """
    if any(size < 1 for size in class_sizes):
        raise ValueError("setiap kelas minimal berisi 1 karakter")
    total = sum(class_sizes)
    count = 0
    for r in range(len(class_sizes) + 1):
        for subset in combinations(class_sizes, r):
            count += (-1) ** r * (total - sum(subset)) ** length
    return count


def acceptance_probability(class_sizes: Sequence[int], length: int) -> float:
    """Peluang satu percobaan acak lolos aturan "minimal satu per kelas"."""
    total = sum(class_sizes)
    return float(Fraction(valid_count(class_sizes, length), total**length))


def rule_constrained_entropy(class_sizes: Sequence[int], length: int) -> float:
    """Entropi setelah rejection sampling: log2(jumlah string yang valid).

    Sama dengan charset_entropy + log2(peluang lolos), sehingga aturan situs
    selalu mengurangi entropi, tidak pernah menambah.
    """
    count = valid_count(class_sizes, length)
    if count == 0:
        raise ValueError("tidak ada string valid: length lebih kecil dari jumlah kelas")
    return math.log2(count)


def strength_label(bits: float) -> str:
    """Label kekuatan sesuai ambang project: <60 lemah, 60-79 cukup, >=80 kuat."""
    if bits < MIN_BITS:
        return "lemah"
    if bits < STRONG_BITS:
        return "cukup"
    return "kuat"