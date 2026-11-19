// All visible text of the demo, in English and Indonesian.

export const STRINGS = {
  en: {
    title: "LocalKey web demo",
    tagline: "A password generator written in Python, running in your browser.",
    loading: "Loading the Python runtime (about 10 MB, first visit only)...",
    loadFailed: "Could not load the Python runtime. Check your connection and reload.",
    length: "Length",
    lower: "a-z",
    upper: "A-Z",
    digits: "0-9",
    symbols: "Symbols",
    excludeAmbiguous: "Avoid look-alikes (0 O o 1 l I |)",
    requireEach: "At least one of each selected type",
    generate: "Generate",
    copy: "Copy",
    copied: "Copied",
    entropy: "Entropy",
    bits: "bits",
    weak: "weak",
    fair: "fair",
    strong: "strong",
    errNoClass: "Select at least one character type.",
    errLengthTooShort: "Length must be at least the number of selected types.",
    errGeneric: "Something went wrong. Try other settings.",
    privacyNote:
      "The password is created on your device and is never sent anywhere.",
    source: "Source code on GitHub",
  },
  id: {
    title: "Demo web LocalKey",
    tagline: "Generator password yang ditulis dengan Python, berjalan di browser Anda.",
    loading: "Memuat runtime Python (sekitar 10 MB, hanya saat kunjungan pertama)...",
    loadFailed: "Runtime Python gagal dimuat. Periksa koneksi lalu muat ulang.",
    length: "Panjang",
    lower: "a-z",
    upper: "A-Z",
    digits: "0-9",
    symbols: "Simbol",
    excludeAmbiguous: "Hindari karakter mirip (0 O o 1 l I |)",
    requireEach: "Minimal satu dari tiap jenis yang dipilih",
    generate: "Buat",
    copy: "Salin",
    copied: "Tersalin",
    entropy: "Entropi",
    bits: "bit",
    weak: "lemah",
    fair: "cukup",
    strong: "kuat",
    errNoClass: "Pilih minimal satu jenis karakter.",
    errLengthTooShort: "Panjang minimal sama dengan jumlah jenis yang dipilih.",
    errGeneric: "Terjadi kesalahan. Coba pengaturan lain.",
    privacyNote:
      "Password dibuat di perangkat Anda dan tidak pernah dikirim ke mana pun.",
    source: "Kode sumber di GitHub",
  },
};

export function pickLanguage(navLang) {
  return typeof navLang === "string" && navLang.toLowerCase().startsWith("id")
    ? "id"
    : "en";
}

const STRENGTH = { lemah: "weak", cukup: "fair", kuat: "strong" };

export function strengthKey(label) {
  const key = STRENGTH[label];
  if (!key) throw new Error(`unknown strength label: ${label}`);
  return key;
}
