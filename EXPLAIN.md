# How LocalKey Works

A walkthrough of the code as of version 0.1.0, which ships the `random` mode. For what LocalKey is meant to become, see [SPEC.md](SPEC.md).

## The three layers

| Layer | File | Job |
|---|---|---|
| Math | `entropy.py` | computes bits, never generates anything random |
| Logic | `generators.py` | builds passwords |
| Interface | `cli.py` | reads terminal arguments and prints results |

Each layer can be tested on its own. A future web or GUI front end could reuse `entropy.py` and `generators.py` unchanged.

## Folder structure

```
localkey/
├── pyproject.toml
├── README.md
├── SPEC.md
├── EXPLAIN.md
├── src/localkey/
│   ├── __init__.py
│   ├── __main__.py
│   ├── entropy.py
│   ├── generators.py
│   └── cli.py
└── tests/
    ├── test_entropy.py
    ├── test_generators.py
    └── test_cli.py
```

The code lives under `src/` on purpose. Without it, Python can import the package straight from the project folder instead of the installed copy, and tests may pass against code that would break once installed. With the src layout, tests always run against the installed package.

## `pyproject.toml`

- `[project]` declares the name, version, and `requires-python = ">=3.10"`. The `dependencies` list is empty: the core uses only the standard library.
- `[project.optional-dependencies]` holds `dev` (pytest, pytest-cov, ruff, mypy) and `clipboard` (pyperclip, for a planned feature).
- `[project.scripts]` contains `localkey = "localkey.cli:main"`. This line creates the `localkey` command when the package is installed.
- `[tool.*]` configures pytest, ruff, and mypy in strict mode.

`pip install -e .` installs in editable mode, so code changes take effect without reinstalling.

## `__init__.py` and `__main__.py`

`__init__.py` re-exports `Result` and `random_password`, so other code can write `from localkey import random_password`.

`__main__.py` makes `python -m localkey random` work. It calls `main()` and passes the return value to `sys.exit`.

## `entropy.py`

Every function here is deterministic: the same input always returns the same output.

`MIN_BITS = 60` and `STRONG_BITS = 80` are the strength thresholds.

### Basic formulas

- `charset_entropy(size, length)` returns `length * log2(size)`. Sixteen characters from 94 give about 104.9 bits.
- `wordlist_entropy(list_size, word_count)` is the same formula applied to words. It is ready for the `phrase` mode.
- `case_entropy(n)` returns `n`: random letter case adds 1 bit per letter.
- `permutation_entropy(k)` returns `log2(k!)`, the entropy of shuffling k items.

### Counting passwords that pass the site rule

`valid_count(class_sizes, length)` counts strings that contain at least one character from every class. It uses inclusion-exclusion:

```
valid = sum over every subset S of the classes:
        (-1)^|S| * (N - size of S)^length
```

With two classes A and B this reads: all strings, minus those with no A, minus those with no B, plus those with neither. The last term is added back because the two subtractions removed it twice. Four classes produce 2^4 = 16 terms.

Python integers have no size limit, so the result is exact even when `94^20` has 40 digits.

The functions built on it:

- `acceptance_probability(...)` returns `valid / N^length`, the chance that one random candidate passes.
- `rule_constrained_entropy(...)` returns `log2(valid)`. It is always a little lower than the entropy without the rule, because the rule removes outputs.
- `strength_label(bits)` returns `"lemah"` (weak), `"cukup"` (fair), or `"kuat"` (strong). The labels are in Indonesian.

## `generators.py`

All randomness in the project happens in this file.

### Character sets

`LOWERCASE` (26), `UPPERCASE` (26), `DIGITS` (10), and `SYMBOLS` (32) come from Python's `string` module rather than hand-typed strings, which rules out typos.

### `RandomSource`

A `Protocol` that only requires a `choice()` method. Two objects satisfy it:

- `secrets.SystemRandom()` in production, which draws from the operating system's CSPRNG.
- `random.Random(seed)` in tests, which repeats the same sequence for the same seed. It is not safe for real passwords.

Passing the random source in as an argument is dependency injection. It lets tests check exact outputs and force rare branches.

### `Result`

A frozen dataclass with `value` and `entropy_bits`.

- `frozen=True` stops the fields from being changed after creation.
- `field(repr=False)` keeps the password out of `repr()`, so printing or logging the object does not expose it.
- The `strength` property calls `strength_label`.

### `random_password()`

1. Collect the enabled character sets.
2. Validate the input. At least one set must be enabled, the length must be at least 1, and when every set is required the length must be at least the number of sets. Four sets cannot fit in three characters.
3. Join the sets into one alphabet.
4. Run rejection sampling: build a full random candidate, check that every set appears, and start over if one is missing. `max_attempts` caps the loop so it cannot run forever.
5. Compute entropy with `rule_constrained_entropy` when the rule is on, or `charset_entropy` when it is off.
6. Return a `Result`.

Inserting one digit and one symbol at fixed spots would be simpler, but an attacker could predict those positions, and the entropy math would get messy. Rejection sampling keeps every valid password equally likely.

`_covers_all()` checks coverage with set intersection (`&`). The leading underscore marks it as internal.

## `cli.py`

### `build_parser()`

Builds the argument parser with `argparse`.

- Global options go before the mode name: `--min-bits`, `--strict`, `--show-entropy`.
- The `random` subcommand takes `-l`, `--no-lower`, `--no-upper`, `--no-digits`, `--no-symbols`, and `--no-require`.
- `required=True` on the subparsers makes the mode mandatory.

### `main(argv)`

1. Parse the arguments. Tests pass `argv` directly instead of running a real terminal.
2. Set the threshold: 80 with `--strict`, otherwise `--min-bits`.
3. Call `random_password`. A `ValueError` prints an error and returns 2.
4. If entropy is below the threshold, print an error and return 1. The password is never printed.
5. Print the password to stdout and, with `--show-entropy`, the entropy to stderr.
6. Return 0.

## One full run

What happens when you type `localkey --show-entropy random -l 16`:

1. The shell finds the `localkey` command that `[project.scripts]` installed.
2. Python calls `localkey.cli.main()`.
3. `argparse` reads `show_entropy=True`, `mode="random"`, `length=16`.
4. The threshold is 60.
5. `random_password(16)` builds a 94-character alphabet, lets `SystemRandom` pick 16 characters, and repeats until all four sets appear. Entropy is `log2(valid_count([26, 26, 10, 32], 16))`, about 104.6 bits.
6. 104.6 is at least 60, so the password passes.
7. stdout gets the password.
8. stderr gets `104.6 bit (kuat)`.
9. The exit code is 0.

Without the rule, 16 characters would give 104.9 bits. Requiring every set costs about 0.3 bits.

## Tests

There are 29 tests.

### `test_entropy.py`

- Checks formulas against numbers you can work out by hand: `94^8` gives 52.44 bits and 6 EFF words give 77.55 bits.
- Compares `valid_count` with brute force. On small alphabets the test enumerates every possible string and counts the valid ones. Any mistake in the inclusion-exclusion formula breaks this test.
- Confirms that length 3 with four required sets gives 0 valid strings and raises an error.
- Confirms the rule costs less than 0.5 bits at length 20.
- Checks the label boundaries at exactly 60 and 80.

### `test_generators.py`

- Length and characters match the request.
- 500 passwords of length 4 all contain every set.
- The same seed produces the same password.
- Disabled sets never appear.
- Reported entropy matches the formula.
- Without a seed, 20 passwords are all different.
- Invalid arguments raise `ValueError`.
- A fake source that always returns `"a"` forces the `RuntimeError` branch when attempts run out.
- `repr()` does not contain the password.

### `test_cli.py`

- stdout holds only the password, and the word "bit" appears only in stderr.
- 8 characters (51.3 bits) are rejected with exit code 1.
- 10 characters (about 65 bits) pass by default and fail with `--strict`.
- Length 0 returns exit code 2.

## Development commands

| Command | Purpose |
|---|---|
| `pytest` | run the tests |
| `pytest --cov=localkey` | run the tests with a coverage report |
| `ruff check .` | lint for common bugs and style problems |
| `ruff format .` | format the code |
| `mypy src` | type-check against the type hints |

## Not built yet

`phrase` mode, `anchor` mode, clipboard support, and the Indonesian wordlist script. [SPEC.md](SPEC.md) describes each one.
