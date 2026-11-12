# LocalKey

A command-line password generator written in Python. It reports the entropy of every password it makes and refuses to print one below 60 bits.

LocalKey runs entirely on your machine. It has no network code, no storage, and no logging. The only dependency of the core package is the Python standard library.

Version 0.1.0 ships the `random` mode. Passphrases and anchor-word passwords are planned (see [Roadmap](#roadmap)).

## Install

LocalKey needs Python 3.10 or newer. It is not on PyPI yet, so install it from a clone or an unzipped copy of the repository.

Run these commands from the folder that contains `pyproject.toml`.

macOS and Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

The `[dev]` extra adds pytest, ruff, mypy, and scipy. If you only want the generator, use `pip install -e .`.

If PowerShell refuses to run the activation script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

## Usage

```console
$ localkey --show-entropy random -l 16
BSCg]7dIlk.5zu,_
104.6 bit (kuat)

$ localkey --show-entropy random -l 16 --exclude-ambiguous
h/`9UpTX8DPivX?_
102.7 bit (kuat)

$ localkey --show-entropy random -l 20 --no-symbols
lmeWE1uDZpWuZV7yL0KA
119.0 bit (kuat)

$ localkey random -l 8
error: entropi 51.3 bit di bawah ambang 60 bit. Tambah panjang atau jenis karakter.
```

The password goes to stdout. The entropy line and any error go to stderr, so `localkey random | clip` (Windows) or `localkey random | pbcopy` (macOS) copies only the password.

The default length is 20. The last command above printed nothing and exited with code 1, because 8 characters give 51.3 bits.

### Language of the output

Strength labels and messages are currently in Indonesian:

| Output | Meaning |
|---|---|
| `lemah` | weak, below 60 bits |
| `cukup` | fair, 60 to 79 bits |
| `kuat` | strong, 80 bits or more |
| `error: entropi X bit di bawah ambang Y bit` | entropy X is below the threshold of Y bits |
| `error: Panjang minimal 1.` | the length must be at least 1 |

### Options for `random`

| Option | Meaning |
|---|---|
| `-l`, `--length` | password length (default 20) |
| `--no-lower` | leave out lowercase letters |
| `--no-upper` | leave out uppercase letters |
| `--no-digits` | leave out digits |
| `--no-symbols` | leave out symbols |
| `--exclude-ambiguous` | drop characters that are easy to misread: `0 O o 1 l I \|` |
| `--no-require` | do not force at least one character from each enabled set |

### Global options

These go before the mode name, for example `localkey --strict random`.

| Option | Meaning |
|---|---|
| `--min-bits N` | reject passwords below N bits (default 60) |
| `--strict` | reject passwords below 80 bits |
| `--show-entropy` | print the entropy and strength label to stderr |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | entropy below the threshold, nothing printed |
| 2 | invalid arguments, such as a length of 0 |

## How entropy is calculated

LocalKey assumes the attacker knows your settings: the length, the character sets, and the rules. The only unknown is the outcome of each random choice. Entropy is then the base-2 logarithm of the number of equally likely passwords:

```
entropy = log2(number of possible passwords)
```

Without rules, that is `length * log2(alphabet size)`. The full alphabet has 94 characters, so each one is worth about 6.55 bits.

By default every password must contain at least one lowercase letter, one uppercase letter, one digit, and one symbol. LocalKey enforces this with rejection sampling: it builds a full random candidate, throws it away if a set is missing, and repeats. Required characters can land anywhere, and every valid password is equally likely.

The rule removes some outputs, so LocalKey counts the valid passwords exactly with inclusion-exclusion and takes the logarithm of that count. For 20 characters the rule costs under 0.5 bits.

`--exclude-ambiguous` shrinks the four sets to 24, 24, 8, and 31 characters (87 in total). A 20-character password then carries 128.6 bits instead of 130.9.

[EXPLAIN.md](EXPLAIN.md) walks through the formulas and the code in detail.

## Randomness

All randomness comes from `secrets.SystemRandom`, which reads from the operating system's cryptographic random source. Tests pass in a seeded generator instead, and that generator is never used outside the test suite.

The test suite includes a chi-square goodness-of-fit test on 100,000 characters. A seeded uniform source must pass it, and a source with a 2% bias toward one character must fail it. Two further tests run the same check against `secrets.choice` and against `random_password` with the site rule turned off. Those two use real randomness and fail by chance about once in a thousand runs, so they are excluded from the default run:

```bash
pytest -m statistical
python scripts/check_uniformity.py
```

With the site rule on, per-character frequencies are not uniform: digits appear more often than letters. That is expected. Rejection sampling discards candidates without a digit, and digits are a small share of the alphabet. What matters is that every valid password is equally likely, and that still holds. [EXPLAIN.md](EXPLAIN.md) has the full explanation.

## Development

```bash
pytest                                  # 34 tests
pytest --cov=localkey                   # with a coverage report
pytest -m statistical                   # chi-square tests with real randomness
ruff check . && ruff format --check .
mypy src tests scripts
```

Project layout:

```
src/localkey/
  entropy.py       entropy formulas, no randomness
  generators.py    password generators, the only place randomness happens
  cli.py           argument parsing and output
tests/
scripts/
  check_uniformity.py   prints chi-square results
```

## Documentation

| File | Contents |
|---|---|
| [SPEC.md](SPEC.md) | requirements and design decisions, including planned modes |
| [EXPLAIN.md](EXPLAIN.md) | a file-by-file walkthrough of the code |

## Roadmap

- [x] `random` mode with the site rule and `--exclude-ambiguous`
- [ ] `phrase` mode: passphrases from the EFF wordlist and an Indonesian wordlist
- [ ] `anchor` mode: a word you choose, such as `cassandra`, wrapped in random characters with random letter case
- [ ] `--copy` to copy the result to the clipboard and clear it after a delay
