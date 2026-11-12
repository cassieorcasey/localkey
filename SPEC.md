# LocalKey Specification

LocalKey is a command-line password generator written in Python. The package and the terminal command are both named `localkey`.

This file records what LocalKey should do and the decisions behind it. Each section says whether the feature is implemented or planned.

## Goals

- Generate passwords from a cryptographically secure random source.
- Report the entropy of every password, calculated under a strict attacker model.
- Refuse to print a password below a minimum entropy.
- Keep everything local. LocalKey never stores, logs, or sends a password anywhere.

## Non-goals

- Storing passwords. LocalKey is a generator, not a password manager.
- A graphical interface. Other front ends can import the library later.

## Attacker model

Entropy is the base-2 logarithm of the number of equally likely outputs:

```
entropy = log2(number of possible passwords)
```

LocalKey assumes the attacker already knows:

- the mode and its settings (length, character sets, rules),
- any anchor word the user typed in,
- the separator and the output pattern.

The only thing the attacker does not know is the result of each random choice. Anything the user chose by hand contributes 0 bits.

## Strength thresholds

| Entropy | Label | Default behavior |
|---|---|---|
| below 60 bits | weak | rejected |
| 60 to below 80 bits | fair | accepted |
| 80 bits or more | strong | accepted |

`--min-bits N` sets a custom threshold. `--strict` sets it to 80.

## Randomness

- Production code uses `secrets.SystemRandom`, which reads from the operating system's CSPRNG.
- Generators accept an injectable random source with a `choice()` method, so tests can pass a seeded `random.Random`. A seeded generator is never used outside tests.

## Mode: `random` (implemented)

Draws each character uniformly from the enabled character sets.

| Set | Size |
|---|---|
| lowercase | 26 |
| uppercase | 26 |
| digits | 10 |
| symbols (`string.punctuation`) | 32 |

All four are enabled by default (94 characters). Default length is 20.

### Site rules

By default every password must contain at least one character from each enabled set. LocalKey enforces this with rejection sampling: generate a full candidate, discard it if any set is missing, and repeat. Required characters can land in any position, and every valid password is equally likely.

The rule removes some outputs, so entropy is computed from the exact count of valid passwords using inclusion-exclusion over the character sets:

```
valid = sum over every subset S of the sets:
        (-1)^|S| * (N - size of S)^length
```

where `N` is the total alphabet size. All arithmetic uses Python integers, so the count is exact. For a 20-character password the rule costs less than 0.5 bits.

`--no-require` turns the rule off. Entropy is then `length * log2(N)`.

### Options

| Option | Meaning |
|---|---|
| `-l`, `--length` | password length |
| `--no-lower`, `--no-upper`, `--no-digits`, `--no-symbols` | disable one character set |
| `--no-require` | do not require one character from each set |
| `--exclude-ambiguous` | drop characters that are easy to misread: `0 O o 1 l I \|` |

### Ambiguous characters

`--exclude-ambiguous` removes `0 O o 1 l I |` from every set before drawing. The sets shrink to 24, 24, 8, and 31 characters (87 total). Entropy is computed from the reduced sizes, so a 20-character password loses about 2.2 bits compared with the full set.

## Testing randomness (implemented)

`tests/test_uniformity.py` runs a chi-square goodness-of-fit test on 100,000 draws. The null hypothesis is that every character has probability 1/k. A p-value below 0.001 counts as evidence of bias.

- Two deterministic tests run with every `pytest` call. A seeded uniform source must pass, and a source with a 2% bias toward one character must fail. Together they show the test can tell the difference.
- Two tests marked `statistical` use real OS randomness: `secrets.choice` directly, and `random_password` with `require_each=False`. They can fail by chance about 0.1% of the time, so they are excluded by default. Run them with `pytest -m statistical`.
- `scripts/check_uniformity.py` prints the full numbers.

`random_password` with the site rule on is expected to fail a per-character chi-square test. That is not a weakness: see "Why the site rule fails the chi-square test" in EXPLAIN.md.

## Mode: `phrase` (planned)

Picks words uniformly from a wordlist and joins them with a separator.

- `--wordlist eff`: the EFF large wordlist, 7,776 words, about 12.9 bits per word.
- `--wordlist id`: an Indonesian wordlist, built by a script from openly licensed sources plus hand curation. Entropy uses the real list size, `log2(N)` per word, so the list does not need exactly 7,776 entries.
- The Indonesian list filters out duplicates, proper names, ambiguous words, and sensitive words, and keeps words of 4 to 8 letters. Each source and its license are recorded in the repository.

Entropy: `word_count * log2(wordlist_size)`.

## Mode: `anchor` (planned)

Builds a password around one or more words the user chooses, for example `cassandra`.

Output pattern:

```
[random prefix][word 1][sep][word 2]...[random suffix]
```

- Spaces inside a word become the separator (default `-`).
- Multiple anchor words are supported.
- The letter case of each anchor letter is randomized.
- `--shuffle` randomizes the order of the words.

Entropy under the strict model:

| Component | Bits |
|---|---|
| random prefix and suffix characters | `count * log2(charset size)` |
| random letter case | 1 per alphabetic letter |
| shuffled word order | `log2(k!)` for k words |
| separator, if picked at random | `log2(choices)` |
| the anchor words | 0 |

Example: `cassandra` and `wishmap` contain 16 letters, giving 16 bits from case. Reaching 60 bits needs 44 more, which takes 7 random characters from the 94-character set (about 45.9 bits). When a password falls short, LocalKey should report the minimum prefix and suffix length that would pass, instead of only rejecting it.

`--show-entropy` prints two numbers for this mode: the strict figure used for the threshold, and a naive figure that assumes the attacker does not know the anchor words. The naive figure is for comparison only.

## Clipboard (planned)

- Installed as an optional extra: `pip install "localkey[clipboard]"` (uses `pyperclip`).
- `--copy` copies the password and clears the clipboard after a set number of seconds.

## Output and exit codes (implemented)

- The password goes to stdout. Entropy and errors go to stderr, so `localkey random | pbcopy` copies only the password.
- The `Result` object hides the password from its `repr`, so printing or logging the object does not leak it.

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | entropy below the threshold |
| 2 | invalid arguments |

## Global options (implemented)

These go before the mode name, for example `localkey --strict random`.

| Option | Meaning |
|---|---|
| `--min-bits N` | reject passwords below N bits (default 60) |
| `--strict` | reject passwords below 80 bits |
| `--show-entropy` | print entropy and strength label to stderr |

## Code layout

```
src/localkey/
  entropy.py     entropy formulas, no randomness
  generators.py  password generators, the only place randomness happens
  cli.py         argument parsing and output
tests/
scripts/
  check_uniformity.py  chi-square report
  build_wordlist.py    (planned)
```

## Roadmap

1. Package layout and the entropy module. Done.
2. `random` mode with rejection sampling, and a minimal CLI. Done.
3. `phrase` mode and the wordlist loader.
4. `anchor` mode with multiple words.
5. Full CLI, clipboard support, and the Indonesian wordlist script.
