# LocalKey web demo: design

Status: draft, waiting for approval. Nothing is built yet.

## Intent

Add a small web demo of LocalKey to the repo. The demo is a progress update
for the owner's Python learning portfolio on GitHub: it shows that the
existing Python code (entropy math, generator) runs unchanged in a browser,
with no server.

Audience: people who open the repo or the GitHub Pages link (recruiters,
reviewers, peers). Not a daily-use password tool.

## Goals

- One static page, hosted on GitHub Pages, that generates a password in the
  browser using the project's own `entropy.py` and `generators.py`.
- Controls: length, the four character classes, `exclude-ambiguous`,
  `require-each`.
- Output: the password, entropy in bits, strength label (lemah / cukup /
  kuat), a copy button, a regenerate button.
- A single source of truth for the logic: no second implementation of the
  entropy math.
- The privacy claim stays true: the password is created and stays on the
  visitor's device.

## Non-goals

- `phrase` and `anchor` modes (not built in the CLI yet; the web gets them
  when the CLI does).
- Accounts, saving, history, analytics, any backend.
- A polished product UI. Clean and readable is enough.
- Replacing the CLI as the main interface.

## Anti-goals

- Never send a password over the network or log it.
- Never use `Math.random` or a seeded generator for real output.
- Do not fork the entropy rules into JavaScript.

## Constraints

- No dependency changes to the core package (`dependencies = []` stays).
- Pyodide is loaded from jsDelivr (about 10 MB on first load, then cached by
  the browser). Pin one exact version.
- Python 3.10+ compatibility of the core stays as is.
- The interface text on the page is a decision for the owner (see below).

## Approaches considered

| | A. Pyodide | B. JavaScript port |
|---|---|---|
| Logic | the real Python files | rewritten in JS |
| Duplication | none | entropy and inclusion-exclusion twice, needs a parity test |
| Load | about 10 MB first visit | tiny |
| Portfolio story | "my Python runs in the browser" | "I also wrote JS" |
| Risk | RNG source must be verified | drift between two copies |

Picked: **A, Pyodide.** The owner chose it in conversation. Reason: it
demonstrates the learning project itself and keeps one source of truth.

## How it works (the decisions made)

Decided by the owner: Pyodide, demo purpose, `random` mode only.

My calls (open to correction):

1. **Folder:** `web/` with `index.html`, `app.js`, `style.css`. No framework,
   no bundler.
2. **Source sharing:** `scripts/build_web.py` copies `src/localkey/entropy.py`
   and `src/localkey/generators.py` into `web/py/localkey/`, so the page loads
   exactly what the tests cover. The copies are generated, not hand-edited.
3. **Bridge:** `app.js` loads Pyodide, writes the copied files into its
   virtual filesystem, imports `localkey`, and calls `random_password(...)`
   with the form values. It reads `value`, `entropy_bits`, `strength` from the
   result and shows them.
4. **Errors:** a `ValueError` from the core (for example length below the
   number of enabled classes) is shown as an inline message, not a crash.
5. **Threshold:** the page shows the label only. It does not refuse to show a
   weak password the way the CLI does, since the demo is for exploring. The
   weak label is visually obvious.
6. **Hosting:** GitHub Pages deployed by a GitHub Actions workflow that runs
   `build_web.py` and publishes `web/`.
7. **Loading state:** a visible "loading Python runtime" message, because the
   first load takes a few seconds.
8. **Docs:** revise the `SPEC.md` non-goal ("A graphical interface") to
   say the web demo exists and is a thin front end over the same core; add a
   short README section with the demo link and how it works.

## Verification before building (first task of the plan)

A small spike, throwaway, before anything else: in a browser, confirm that
under Pyodide `os.urandom` and `secrets.SystemRandom().choice` return
different values on every call and are backed by the browser's
`crypto.getRandomValues`. If this cannot be confirmed, stop and bring the
choice back to the owner (fallback: pass JS random values into Python through
an injected `RandomSource`, which the core already supports).

## Testing

- Existing 34 Python tests stay green and remain the logic tests.
- A Node-based or browser smoke test: the page loads, generates a password of
  the requested length, shows entropy and label, and shows an error for an
  impossible combination.
- Manual check in two browsers.

## Left to the builder

Exact styling, wording of messages, file names inside `web/`, workflow
details, the Pyodide version pin.

## Language (decided by the owner: both Indonesian and English)

- The page ships in English and Indonesian with a visible EN / ID toggle.
- My calls: the default comes from the browser language (`id*` gives
  Indonesian, anything else English). Strings live in one small dictionary in
  `app.js`, no i18n library. The choice is not stored anywhere.
- The core's strength labels stay as they are (`lemah` / `cukup` / `kuat`).
  The page maps them to display text: weak / fair / strong in English. No
  threshold logic is copied into JavaScript.
- Error messages from the core are Indonesian or English today depending on
  where they come from; the page shows its own translated message keyed on the
  kind of error, so the toggle covers everything the visitor sees.
- Test: the smoke test runs once per language and checks that no key is
  missing in either dictionary.

## Open for the owner

Nothing open. Waiting for approval of this document.
