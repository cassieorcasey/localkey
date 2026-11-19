import { test } from "node:test";
import assert from "node:assert/strict";
import { STRINGS, pickLanguage, strengthKey } from "../i18n.js";

test("en and id have the same keys", () => {
  assert.deepEqual(Object.keys(STRINGS.en).sort(), Object.keys(STRINGS.id).sort());
});

test("no empty strings", () => {
  for (const lang of ["en", "id"]) {
    for (const [key, value] of Object.entries(STRINGS[lang])) {
      assert.ok(value.trim().length > 0, `${lang}.${key} is empty`);
    }
  }
});

test("pickLanguage", () => {
  assert.equal(pickLanguage("id-ID"), "id");
  assert.equal(pickLanguage("id"), "id");
  assert.equal(pickLanguage("en-US"), "en");
  assert.equal(pickLanguage("fr"), "en");
  assert.equal(pickLanguage(undefined), "en");
});

test("strengthKey maps core labels", () => {
  assert.equal(strengthKey("lemah"), "weak");
  assert.equal(strengthKey("cukup"), "fair");
  assert.equal(strengthKey("kuat"), "strong");
  assert.throws(() => strengthKey("mantap"));
});
