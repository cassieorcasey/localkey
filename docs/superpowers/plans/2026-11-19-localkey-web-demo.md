# LocalKey Web Demo Implementation Plan

> **For agentic workers:** execute task by task, in order. Each task ends with
> a check that must pass before the next starts. Spec:
> `docs/superpowers/specs/2026-11-19-localkey-web-demo-design.md` (approved).

**Goal:** a static, bilingual (EN/ID) GitHub Pages demo that runs the real
`entropy.py` and `generators.py` in the browser through Pyodide.

**Architecture:** `scripts/build_web.py` copies two core files into
`web/py/localkey/`. `web/bridge.js` (pure, testable) calls Python through a
Pyodide instance. `web/i18n.js` holds the EN/ID dictionary. `web/app.js` wires
the DOM. No framework, no bundler, no backend.

**Rules for every task:** touch only the files listed; keep the core package
unchanged (`dependencies = []`); existing 34 tests stay green; no
`Math.random` anywhere.

## File map

| File | Responsibility |
|---|---|
| `scripts/build_web.py` | copy `entropy.py`, `generators.py`, `__init__.py` stub into `web/py/localkey/` |
| `tests/test_build_web.py` | generated copies equal the sources |
| `web/bridge.js` | `generate(pyodide, options)` returns `{value, entropyBits, strength}` or `{error}` |
| `web/i18n.js` | `STRINGS = {en: {...}, id: {...}}`, `pickLanguage(navLang)`, `strengthKey(label)` |
| `web/index.html`, `web/style.css`, `web/app.js` | page, look, DOM wiring |
| `web/test/*.mjs` | Node tests: i18n parity, bridge against real Pyodide |
| `web/package.json` | dev-only: `pyodide` (pinned), test script |
| `.github/workflows/pages.yml` | build and deploy `web/` |

---

## Task 1: Spike, is Pyodide's randomness the browser's? (throwaway)

Purpose: the whole design rests on this. Nothing from this task is kept.

**Files:** `web/spike.html` (deleted at the end of the task).

- [ ] Write `spike.html`: load Pyodide from jsDelivr (pin the current stable
  version), and before loading wrap `crypto.getRandomValues` with a counter:
  ```js
  let calls = 0;
  const orig = crypto.getRandomValues.bind(crypto);
  crypto.getRandomValues = (a) => { calls++; return orig(a); };
  ```
- [ ] Run in Python: `import os, secrets; a=os.urandom(16); b=os.urandom(16);
  c=secrets.SystemRandom().choice("abcdefghij")` and print `a != b` and the
  counter value from JS before and after.
- [ ] Serve with `python -m http.server` and open in Chrome.
- [ ] **Verify:** `a != b` is true and `calls` increased after the Python
  calls. Record the Pyodide version and the numbers in the ledger
  (`docs/superpowers/plans/ledger.md`).
- [ ] **If calls did not increase:** STOP. Report to the owner. Fallback is an
  injected `RandomSource` fed by `crypto.getRandomValues`; that changes the
  design and needs approval.
- [ ] Delete `web/spike.html`.

## Task 2: `build_web.py` (TDD)

**Files:** create `scripts/build_web.py`, `tests/test_build_web.py`.

- [ ] Write the failing test: run `build_web.build(dest=tmp_path)`; assert
  `tmp_path/localkey/entropy.py` and `generators.py` have bytes identical to
  `src/localkey/`, and `__init__.py` exists and exports `random_password`.
- [ ] Run `pytest tests/test_build_web.py`; expect failure (module missing).
- [ ] Implement `build(dest: Path = Path("web/py")) -> None`. The generated
  `__init__.py` is `from .generators import Result, random_password`. A
  `main()` calls `build()`. Use `pathlib` and `shutil.copyfile` only.
- [ ] Run `pytest`; expect 35 passed (34 + new).
- [ ] Run `ruff check . && ruff format --check . && mypy src` (scripts are
  not in mypy scope; keep the script typed anyway).
- [ ] Commit: "Add build_web script".

## Task 3: i18n module (TDD)

**Files:** create `web/i18n.js`, `web/test/i18n.test.mjs`, `web/package.json`.

- [ ] `web/package.json`: `"type": "module"`, `"private": true`,
  `"scripts": {"test": "node --test test/"}`, devDependency `pyodide` pinned
  to the Task 1 version.
- [ ] Failing tests (Node's built-in `node:test`):
  - `en` and `id` have exactly the same keys.
  - no value is an empty string.
  - `pickLanguage("id-ID") === "id"`, `pickLanguage("id") === "id"`,
    `pickLanguage("en-US") === "en"`, `pickLanguage("fr") === "en"`,
    `pickLanguage(undefined) === "en"`.
  - `strengthKey("lemah") === "weak"`, `"cukup" -> "fair"`, `"kuat" ->
    "strong"`; unknown label throws.
- [ ] Implement. Required keys: `title`, `loading`, `length`, `lower`,
  `upper`, `digits`, `symbols`, `excludeAmbiguous`, `requireEach`,
  `generate`, `copy`, `copied`, `entropy`, `bits`, `weak`, `fair`, `strong`,
  `errNoClass`, `errLengthTooShort`, `errGeneric`, `privacyNote`.
- [ ] Run `cd web && npm install && npm test`; expect pass.
- [ ] Commit: "Add EN/ID dictionary".

## Task 4: `bridge.js` against real Pyodide (TDD)

**Files:** create `web/bridge.js`, `web/test/bridge.test.mjs`.

Interface (fixed):
```js
// options: {length, lowercase, uppercase, digits, symbols,
//           requireEach, excludeAmbiguous}
export async function loadCore(pyodide, files) // writes files into FS, imports localkey
export function generate(pyodide, options)
// -> {ok: true, value, entropyBits, strength}  strength in {"lemah","cukup","kuat"}
// -> {ok: false, kind: "noClass" | "lengthTooShort" | "other"}
```

- [ ] Failing tests, using the npm `pyodide` package in Node after running
  `python scripts/build_web.py`:
  - default options (length 20): `value.length === 20`, `entropyBits > 100`,
    `strength === "kuat"`.
  - all four classes off: `{ok:false, kind:"noClass"}`.
  - length 2 with four classes and `requireEach`: `kind:"lengthTooShort"`.
  - `excludeAmbiguous: true`, 500 generations: no result contains any of
    `0 O o 1 l I |`.
  - 50 generations are all distinct.
  - parity: the entropy for length 16, defaults, equals the value the Python
    test suite checks (`valid_count`-based, about 104.6 bits; assert within
    0.1).
- [ ] Implement. Map error kinds by matching on the exception type
  (`ValueError`) and on conditions checked in JS before the call (no class
  enabled; length below enabled class count) so translation never depends on
  the core's message text.
- [ ] Run `npm test`; expect pass.
- [ ] Commit: "Add Pyodide bridge".

## Task 5: Page and wiring

**Files:** create `web/index.html`, `web/style.css`, `web/app.js`.

- [ ] `index.html`: form with the controls from the spec, result area
  (`<output>`), EN/ID toggle, loading message, privacy note. All text comes
  from `i18n.js` via `data-i18n` attributes.
- [ ] `app.js`: pick language from `navigator.language`; load Pyodide from
  jsDelivr (same pinned version as Task 1); fetch the three files under
  `py/localkey/`; call `loadCore`; enable the form; on any control change or
  Generate click call `generate` and render value, entropy with one decimal,
  and the translated strength label with a class for color; Copy uses
  `navigator.clipboard.writeText`; toggle re-renders all text without
  regenerating.
- [ ] Rules: password is only ever written to the `<output>` element; no
  `console.log` of it; no network call other than the Pyodide CDN and the
  local `py/` files.
- [ ] `style.css`: readable, responsive, not decorative. Weak is visibly
  different from strong without relying on color alone (text label stays).
- [ ] Verify in a real browser (Chrome tools or the owner's): page loads,
  generates, toggles language, copies, shows the three error cases. Record
  results in the ledger. This step is not skipped.
- [ ] Commit: "Add web demo page".

## Task 6: Docs

**Files:** modify `SPEC.md` (line 17 non-goal), `README.md`, `EXPLAIN.md`.

- [ ] `SPEC.md`: replace the "A graphical interface" non-goal with a line
  saying a web demo exists as a thin front end over the same core, `random`
  mode only; the CLI remains the primary interface.
- [ ] `README.md` (English): short "Web demo" section: link placeholder for
  the Pages URL, one paragraph on how it works (Pyodide, nothing leaves the
  device), how to build locally (`python scripts/build_web.py`, then
  `python -m http.server -d web`).
- [ ] `EXPLAIN.md`: one paragraph correcting the earlier claim: a web front
  end reuses the core by running it in Pyodide; a plain JS page could not.
- [ ] Commit: "Document web demo".

## Task 7: Deployment

**Files:** create `.github/workflows/pages.yml`.

- [ ] Workflow on push to `main`: checkout, setup-python, run
  `python scripts/build_web.py`, upload `web/` (excluding `test/`,
  `node_modules`, `package*.json`) as the Pages artifact, deploy.
- [ ] Add `web/py/` to `.gitignore` (generated).
- [ ] Verify by running the build step locally and serving the output folder
  to confirm the page works with only the files that would be published.
- [ ] Tell the owner the one manual step: repo Settings, Pages, Source:
  GitHub Actions.
- [ ] Commit: "Add Pages workflow".

## Task 8: Final verification

- [ ] `pytest` (35 passed), `pytest -m statistical` still passes,
  `ruff check .`, `ruff format --check .`, `mypy src`, `cd web && npm test`.
- [ ] Manual pass in two browsers: both languages, all controls, copy, error
  cases, throttled network to confirm the loading message shows.
- [ ] Confirm in the browser network tab that, after load, generating a
  password makes no network request.
- [ ] Report results to the owner with the evidence, not a summary of effort.
