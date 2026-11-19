import { CORE_FILES, generate, loadCore } from "./bridge.js";
import { STRINGS, pickLanguage, strengthKey } from "./i18n.js";

const PYODIDE_VERSION = "314.0.8";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

const $ = (id) => document.getElementById(id);
const form = $("options");

let lang = pickLanguage(navigator.language);
let statusKey = "loading";
let last = null; // last result from generate(), re-rendered on language switch
let pyodide = null;

function t(key) {
  return STRINGS[lang][key];
}

function render() {
  document.documentElement.lang = lang;
  document.title = t("title");
  for (const el of document.querySelectorAll("[data-i18n]")) {
    el.textContent = t(el.dataset.i18n);
  }
  for (const btn of document.querySelectorAll("[data-lang]")) {
    btn.setAttribute("aria-pressed", String(btn.dataset.lang === lang));
  }
  $("status").textContent = statusKey ? t(statusKey) : "";
  $("status").hidden = !statusKey;
  renderResult();
}

const ERROR_KEYS = {
  noClass: "errNoClass",
  lengthTooShort: "errLengthTooShort",
  other: "errGeneric",
};

function renderResult() {
  const ok = last?.ok === true;
  $("password").textContent = ok ? last.value : "";
  $("copy").disabled = !ok;
  $("meter").hidden = !ok;
  $("error").hidden = !last || ok;
  if (ok) {
    const key = strengthKey(last.strength);
    $("bits").textContent = last.entropyBits.toFixed(1);
    $("strength").textContent = t(key);
    $("strength").className = `strength ${key}`;
  } else if (last) {
    $("error").textContent = t(ERROR_KEYS[last.kind]);
  }
}

function readOptions() {
  const checked = (id) => $(id).checked;
  return {
    length: Number.parseInt($("length").value, 10) || 0,
    lowercase: checked("lowercase"),
    uppercase: checked("uppercase"),
    digits: checked("digits"),
    symbols: checked("symbols"),
    requireEach: checked("requireEach"),
    excludeAmbiguous: checked("excludeAmbiguous"),
  };
}

function regenerate() {
  last = generate(pyodide, readOptions());
  renderResult();
}

async function start() {
  render();
  try {
    const { loadPyodide } = await import(`${PYODIDE_URL}pyodide.mjs`);
    pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
    const files = {};
    for (const name of CORE_FILES) {
      const res = await fetch(`py/localkey/${name}`);
      if (!res.ok) throw new Error(`missing py/localkey/${name}`);
      files[name] = await res.text();
    }
    await loadCore(pyodide, files);
  } catch (err) {
    console.error(err);
    statusKey = "loadFailed";
    render();
    return;
  }
  statusKey = null;
  form.hidden = false;
  render();
  regenerate();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  regenerate();
});
form.addEventListener("change", regenerate);

$("copy").addEventListener("click", async () => {
  if (last?.ok !== true) return;
  await navigator.clipboard.writeText(last.value);
  $("copy").textContent = t("copied");
  setTimeout(() => ($("copy").textContent = t("copy")), 1500);
});

for (const btn of document.querySelectorAll("[data-lang]")) {
  btn.addEventListener("click", () => {
    lang = btn.dataset.lang;
    render();
  });
}

start();
