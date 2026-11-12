# LocalKey

Generator password di terminal. Setiap password yang dibuat ikut dihitung entropinya, dan LocalKey menolak mencetak password di bawah 60 bit.

Saat ini baru ada mode `random`. Mode passphrase dan kata jangkar sedang dikerjakan.

## Instal

Butuh Python 3.10 atau lebih baru.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Contoh

```console
$ localkey --show-entropy random -l 16
D+A;))~S}sR9BNB-
104.6 bit (kuat)

$ localkey --show-entropy random -l 16 --no-symbols
Uzt9NF2ZdVguLVbB
95.2 bit (kuat)

$ localkey random -l 8
error: entropi 51.3 bit di bawah ambang 60 bit. Tambah panjang atau jenis karakter.
```

Password keluar lewat stdout, sedangkan angka entropi dan pesan error lewat stderr. Jadi `localkey random | pbcopy` hanya menyalin password-nya.

### Opsi

| Opsi | Fungsi |
|---|---|
| `-l`, `--length` | panjang password, default 20 |
| `--no-lower`, `--no-upper`, `--no-digits`, `--no-symbols` | buang satu jenis karakter |
| `--no-require` | jangan paksa minimal satu karakter dari tiap jenis |
| `--min-bits N` | ambang penolakan, default 60 |
| `--strict` | ambang jadi 80 |
| `--show-entropy` | cetak entropi dan labelnya |

`--min-bits`, `--strict`, dan `--show-entropy` ditulis sebelum `random`.

### Kode keluar

- `0`: berhasil
- `1`: entropi di bawah ambang
- `2`: argumen tidak valid, misalnya panjang 0

## Cara menghitung entropi

LocalKey menganggap penyerang sudah tahu charset dan aturan yang dipakai. Yang tidak ia tahu hanya hasil acaknya. Entropi = log₂(jumlah password yang mungkin keluar).

Tanpa aturan, rumusnya `panjang × log₂(ukuran charset)`. Charset penuh berisi 94 karakter, jadi tiap karakter bernilai sekitar 6,55 bit.

Secara default LocalKey mewajibkan minimal satu huruf kecil, satu huruf besar, satu angka, dan satu simbol. Kandidat yang tidak memenuhi aturan dibuang lalu diulang (rejection sampling), jadi posisi karakter wajib tetap acak. Aturan ini memperkecil jumlah password yang mungkin. Jumlahnya dihitung eksak dengan inklusi-eksklusi di `entropy.valid_count`. Untuk 20 karakter, pengurangannya kurang dari 0,5 bit.

| Entropi | Label | Default |
|---|---|---|
| < 60 bit | lemah | ditolak |
| 60 sampai < 80 bit | cukup | diterima |
| ≥ 80 bit | kuat | diterima |

Keacakan berasal dari `secrets.SystemRandom`, yang mengambil byte acak dari sistem operasi.

## Struktur

```
src/localkey/
  entropy.py     rumus entropi, tanpa keacakan
  generators.py  pembuat password
  cli.py         argparse dan output
tests/
```

## Tes

```bash
pytest --cov=localkey
ruff check .
mypy src
```

## Rencana

- [x] Mode `random` dengan aturan minimal satu per jenis karakter
- [ ] Passphrase dari wordlist EFF dan wordlist Bahasa Indonesia
- [ ] Mode kata jangkar, misalnya `cassandra` dengan awalan dan akhiran acak
- [ ] Salin ke clipboard (`--copy`)
