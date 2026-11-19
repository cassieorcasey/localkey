# Ledger: LocalKey web demo

## Task 1: spike (done, throwaway, not kept)
- Pyodide 314.0.8 (Python 3.14.2).
- Headless Chrome: `crypto.getRandomValues` calls went from 11 to 97 while
  Python ran `os.urandom` x2 and 50 `SystemRandom().choice`; two urandom
  outputs differed. Pyodide source confirms: browser -> `crypto.getRandomValues`,
  Node -> `node:crypto.randomFillSync`.
- Result: design holds, no fallback needed.

## Task 2: build_web.py (done)
- Red: 2 failing tests (module missing). Green: 36 passed.
- Fix along the way: ruff E501 in the test, mypy return type in the test.

## Task 3: i18n.js (done)
- First red was for the wrong reason (`node --test test/` is not valid in
  Node 22; changed to `test/*.test.mjs`). Re-ran red properly, then 4 pass.

## Task 4: bridge.js (done)
- 8 tests against real Pyodide 314.0.8 in Node; entropy equals CPython
  exactly (104.5925141352476 and 128.62721670282772).

## Task 5: page (done)
- Headless Chrome, both locales, 29 checks: generate, regenerate, length,
  look-alikes removed, clipboard, no network request while generating, both
  error cases, language toggle, weak label, no page errors, password never
  logged, CDN failure shows the load error.
- Bug found by the checks: `form { display: grid }` overrode `[hidden]`, so
  the form showed before Python loaded and after a load failure. Fixed with
  `[hidden] { display: none !important; }`.
- CDN requests were routed to the same Pyodide version from node_modules
  because jsDelivr is not reachable from the build workspace.

## Task 6: docs (done)
- SPEC non-goal revised + "Web demo" section; README "Web demo" section,
  test count, layout; EXPLAIN layer paragraph corrected.

## Task 7: workflow (done)
- Build step simulated from a clean copy; the 8 published files alone pass
  all 29 browser checks.

## Task 8: final (done)
- pytest 36 passed; statistical 2 passed; ruff clean; mypy src tests
  scripts clean; npm test 12 passed; no Math.random or console.log in web/.
- Not done: a second browser engine (only Chrome is available here).
