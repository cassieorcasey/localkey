// Runs the real Python core inside Pyodide (Node build).
// Needs `python scripts/build_web.py` first, so web/py/ exists.
import { before, test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { loadPyodide } from "pyodide";
import { CORE_FILES, generate, loadCore } from "../bridge.js";

const DEFAULTS = {
  length: 20,
  lowercase: true,
  uppercase: true,
  digits: true,
  symbols: true,
  requireEach: true,
  excludeAmbiguous: false,
};

let py;

before(async () => {
  py = await loadPyodide();
  const files = {};
  for (const name of CORE_FILES) {
    files[name] = await readFile(new URL(`../py/localkey/${name}`, import.meta.url), "utf8");
  }
  await loadCore(py, files);
});

test("default options give a strong 20-character password", () => {
  const r = generate(py, DEFAULTS);
  assert.equal(r.ok, true);
  assert.equal(r.value.length, 20);
  assert.ok(r.entropyBits > 100);
  assert.equal(r.strength, "kuat");
});

test("entropy matches CPython exactly (parity)", () => {
  assert.equal(generate(py, { ...DEFAULTS, length: 16 }).entropyBits, 104.5925141352476);
  assert.equal(
    generate(py, { ...DEFAULTS, excludeAmbiguous: true }).entropyBits,
    128.62721670282772,
  );
});

test("no character type selected", () => {
  const off = { lowercase: false, uppercase: false, digits: false, symbols: false };
  assert.deepEqual(generate(py, { ...DEFAULTS, ...off }), { ok: false, kind: "noClass" });
});

test("length shorter than the selected types", () => {
  assert.deepEqual(generate(py, { ...DEFAULTS, length: 2 }), {
    ok: false,
    kind: "lengthTooShort",
  });
});

test("same length is fine when requireEach is off", () => {
  const r = generate(py, { ...DEFAULTS, length: 2, requireEach: false });
  assert.equal(r.ok, true);
  assert.equal(r.value.length, 2);
  assert.equal(r.strength, "lemah");
});

test("excludeAmbiguous removes look-alikes", () => {
  for (let i = 0; i < 500; i++) {
    const { value } = generate(py, { ...DEFAULTS, excludeAmbiguous: true });
    assert.doesNotMatch(value, /[0Oo1lI|]/);
  }
});

test("50 passwords are all different", () => {
  const seen = new Set();
  for (let i = 0; i < 50; i++) seen.add(generate(py, DEFAULTS).value);
  assert.equal(seen.size, 50);
});

test("other core errors are reported, not thrown", () => {
  assert.deepEqual(generate(py, { ...DEFAULTS, length: 0, requireEach: false }), {
    ok: false,
    kind: "other",
  });
});
