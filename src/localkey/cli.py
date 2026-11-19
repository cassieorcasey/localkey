"""Antarmuka baris perintah. Hanya urusan input/output, tanpa logika acak.

Versi ini baru punya subcommand `random`. Mode `phrase` dan `anchor`
menyusul di tahap 3 dan 4.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import entropy
from .generators import random_password


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="localkey", description="LocalKey: password generator."
    )
    parser.add_argument(
        "--min-bits",
        type=float,
        default=entropy.MIN_BITS,
        help="tolak hasil di bawah ambang ini (default 60)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="naikkan ambang ke 80 bit"
    )
    parser.add_argument(
        "--show-entropy", action="store_true", help="tampilkan entropi ke stderr"
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    rand = sub.add_parser("random", help="password acak penuh")
    rand.add_argument("-l", "--length", type=int, default=20)
    rand.add_argument("--no-lower", action="store_true")
    rand.add_argument("--no-upper", action="store_true")
    rand.add_argument("--no-digits", action="store_true")
    rand.add_argument("--no-symbols", action="store_true")
    rand.add_argument(
        "--exclude-ambiguous",
        action="store_true",
        help="buang karakter yang mudah tertukar: 0 O o 1 l I |",
    )
    rand.add_argument(
        "--no-require",
        action="store_true",
        help="jangan wajibkan minimal satu karakter per jenis",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    min_bits = entropy.STRONG_BITS if args.strict else args.min_bits

    try:
        result = random_password(
            args.length,
            lowercase=not args.no_lower,
            uppercase=not args.no_upper,
            digits=not args.no_digits,
            symbols=not args.no_symbols,
            require_each=not args.no_require,
            exclude_ambiguous=args.exclude_ambiguous,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if result.entropy_bits < min_bits:
        print(
            f"error: entropi {result.entropy_bits:.1f} bit di bawah ambang "
            f"{min_bits:.0f} bit. Tambah panjang atau jenis karakter.",
            file=sys.stderr,
        )
        return 1

    # Password ke stdout, info ke stderr: `localkey random | pbcopy` tetap bersih.
    print(result.value)
    if args.show_entropy:
        print(f"{result.entropy_bits:.1f} bit ({result.strength})", file=sys.stderr)
    return 0
