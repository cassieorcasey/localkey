// Thin bridge between the page and the Python core running in Pyodide.
// No password logic lives here: it only passes options in and results out.

export const CORE_FILES = ["__init__.py", "entropy.py", "generators.py"];

const PY_ROOT = "/localkey_core";

let randomPassword = null;

export async function loadCore(pyodide, files) {
  pyodide.FS.mkdirTree(`${PY_ROOT}/localkey`);
  for (const name of CORE_FILES) {
    pyodide.FS.writeFile(`${PY_ROOT}/localkey/${name}`, files[name]);
  }
  pyodide.runPython(`import sys\nsys.path.insert(0, "${PY_ROOT}")`);
  randomPassword = pyodide.pyimport("localkey").random_password;
}

export function generate(pyodide, options) {
  if (!randomPassword) throw new Error("call loadCore first");

  // Checked here so the page can translate them without reading Python's text.
  const classes = [options.lowercase, options.uppercase, options.digits, options.symbols]
    .filter(Boolean).length;
  if (classes === 0) return { ok: false, kind: "noClass" };
  if (options.requireEach && options.length < classes) {
    return { ok: false, kind: "lengthTooShort" };
  }

  let result;
  try {
    result = randomPassword.callKwargs({
      length: options.length,
      lowercase: options.lowercase,
      uppercase: options.uppercase,
      digits: options.digits,
      symbols: options.symbols,
      require_each: options.requireEach,
      exclude_ambiguous: options.excludeAmbiguous,
    });
  } catch (err) {
    if (err instanceof pyodide.ffi.PythonError) return { ok: false, kind: "other" };
    throw err;
  }
  try {
    return {
      ok: true,
      value: result.value,
      entropyBits: result.entropy_bits,
      strength: result.strength,
    };
  } finally {
    result.destroy();
  }
}
