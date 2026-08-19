# Evaluasi Eksperimen 2 — Ekstraksi Deterministis + LLM Hanya untuk Mapping (Qwen2.5-3B)

Eksperimen lanjutan setelah Exp-1. Tujuan: menguji **pendekatan hibrida**
("Opsi C") yang direkomendasikan di akhir `evaluasi_exp1.md` —

- ekstraksi metadata skema dilakukan **oleh kode** (deterministis, tidak
  bergantung pada model),
- LLM (Qwen2.5-3B) **hanya** menyarankan pemetaan ke konsep canonical
  dengan format output kaku.

Pertanyaan yang diuji: apakah membatasi peran LLM pada penalaran mapping
(sekaligus menyuplai skema yang sudah +bersih+ oleh kode) menaikkan
keandalan, khususnya pada kasus sulit Client B (EAV + JSONB) di mana
Exp-1 v2 **gagal** menemukan `Product.name` yang tersembunyi di baris EAV.

## Metode

- Model: Qwen2.5-3B-Instruct-Q4_K_M (CPU-only, llama.cpp, OpenAI-compatible
  di `127.0.0.1:8080`).
- Pipeline (2 tahap, terpisah):
  1. `extractor.py` → mem-parse file SQL (`CREATE TABLE` + `INSERT`) menjadi
     JSON skema deterministis (tabel, kolom, tipe, PK/FK, baris sampel).
     **Bukan parser SQL universal**; cukup untuk format eksperimen.
  2. `mapper.py` → mengirim skema JSON ke LLM, satu prompt dengan instruksi
     `konsep/ditemukan/source/confidence/alasan`, `temperature=0`,
     `seed=42`, `max_tokens=512`.
- Client A (Northwind, kolom jelas): 2 run. Client B (EAV+JSONB, nama
  tersembunyi di baris): 3 run untuk menguji determinisme di kasus sulit.
- LLM sama (Qwen2.5-3B) seperti Exp-1; hanya **tatanan** yang diubah.
- Skema yang disuplai ke LLM adalah hasil ekstraksi **kode**, bukan teks SQL
  mentah yang harus dibaca sendiri oleh model (perbedaan kunci vs Exp-1 yang
  memakai Hermes file-tool).

## Hasil

### Client A (Northwind) — 2 run identik

| Konsep | Hasil (kedua run) | Ground truth (skema) |
|---|---|---|
| Product.name | ditemukan: true, `products.product_name`, tinggi | ✓ |
| Product.price | ditemukan: true, `products.unit_price`, tinggi | ✓ |
| Product.stock | ditemukan: true, `products.units_in_stock`, tinggi | ✓ |

→ **6/6** (2 run × 3 konsep). Deterministik penuh.

### Client B (EAV+JSONB) — 3 run identik

| Konsep | Hasil (ketiga run) | Ground truth (skema) |
|---|---|---|
| Product.name | ditemukan: true, `attr_value_text` (baris EAV) + `objects.object_type="product"`, sedang | ✓ nama ada di baris EAV, bukan kolom bernama |
| Product.price | ditemukan: true, `attr_value_num` via `attribute_code="price"`, sedang | ✓ |
| Product.stock | ditemukan: true, `attr_value_num` via `attribute_code="stock"`, sedang | ✓ |

→ **9/9** (3 run × 3 konsep). Deterministik penuh.

### Usage

- Client A: input 2529 / output 160 / total 2689 per run (cached 2528).
- Client B: input 1477 / output 248 / total 1725 per run.

## Perbandingan dengan Exp-1

| Aspek | Exp-1 (Hermes, prompt v2) | Exp-2 (hibrida) |
|---|---|---|
| Peran LLM | membaca file skema + analisis + konklusi | hanya usulan mapping (skema dari kode) |
| Client A | 2/3 lalu 0/3 (tak andal) | **6/6 deterministik** |
| Client B (EAV) | 0/3 — tahu lokasi tapi tak mau memutuskan | **9/9 deterministik**, lokasi benar |
| Keandalan lintas run | non-deterministik (gagal total di run#2) | identik antar run |

## Temuan Kunci

1. **Pendekatan hibrida "Opsi C" menaikkan keandalan secara nyata** dan
   menjadikan hasil **deterministik**. Dengan `temperature=0` + `seed` tetap
   + skema bersih dari kode + format kaku, Qwen2.5-3B menghasilkan mapping
   benar **konsisten** (A 2/2, B 3/3 run), kontras dengan Exp-1 v2 yang
   jatuh 0/3 pada run berulang dengan prompt identik.

2. **Kasus sulit (EAV/JSONB) kini lolos.** Model berhasil menyimpulkan
   `Product.name` dari baris `attr_value_text` (nama disembunyikan, bukan
   kolom literal) dan memetakan `price`/`stock` lewat `attribute_code`. Ini
   adalah kasus yang sama yang membuat Exp-1 menyimpulkan "3B + prompting
   saja belum cukup" — pada Exp-2 3B **cukup** ketika perannya dipersempit.

3. **Non-determinisme Exp-1 bukan murni kapasitas, melainkan juga tatanan
   tugas.** Mengurangi beban kognitif model (skema sudah dibersihkan &
   distrukturkan) sekaligus format output kaku menghilangkan mode gagal
   "aman-menghindar" yang dominan di Exp-1.

4. **Bug parser pada Exp-2 asli ikut diperbaiki selama penyusunan ini:**
   - `extractor.py` tidak menangani komentar SQL `--`/`/* */` → Client B
     menghasilkan kolom palSU (`--`, `...`) dan baris korup. Diperbaiki
     dengan pembersih komentar yang menghormati string literal.
   - `parse_answer()` (mapper) tidak menormalkan penanda daftar (`### `,
     `-`, `*`) sehingga format kata kunci dengan `## Konsep:` gagal di-parse
     (`parsed: {}` padahal output model benar). Diperbaiki.
   - Hasil di atas memakai pipeline yang sudah diperbaiki.

## Keterbatasan eksperimen

- Skala kecil (A:2 run, B:3 run) pada 2 skema contoh (bukan DB produksi).
- `extractor.py` bukan parser SQL universal; cukup untuk format CREATE/INSERT
  eksperimen. Keandalan ekstraksi pada skema beragam di luar format ini
  belum diuji.
- Usulan mapping dari LLM masih perlu **validasi/manual review** (arah fase
  #11) — eksperimen ini membuktikan usulan akurat & deterministik, bukan
  substitusi untuk konfirmasi klien.
- 3B + tatanan ini berlaku untuk konsep sederhana (name/price/stock);
  generalisasi ke kosakata canonical yang lebih luas belum diuji.

## Verdict untuk fase #11

| Pertanyaan | Jawaban berdasarkan bukti |
|---|---|
| Hibrida (ekstraksi kode + LLM mapping) menaikkan keandalan? | **Ya** — 15/15 usulan benar & deterministik vs Exp-1 yang tak konsisten. |
| Qwen2.5-3B masih layak dipakai? | **Layak** bila peran dibatasi pada mapping dengan format kaku; TIDAK layak untuk parsing/read bebas (Exp-1). |
| Tetap anjurkan model lebih besar? | **Tetap** sebagai lapisan cadangan/untuk kasus ambigu; kebuthan pokok terpenuhi 3B + hibrida. |

**Kesimpulan**: pendekatan hibrida — kode untuk ekstraksi + LLM hanya untuk
penalaran mapping dengan [`temperature=0`]+[seed] + format kaku — mengatasi
akar kegagalan Exp-1 dan menjadikan hasil **andal & deterministik** pada
kedua profil skema (mudah DAN sulit). Ini rekomendasi kuat untuk desain
implementasi fase #11 (AI Schema Analyzer).

## Data pendukung

- `exp2/extractor.py` — ekstraksi deterministis skema.
- `exp2/mapper.py` — LLM mapping (temperature=0, seed=42).
- `exp2/out/schema_a.json`, `exp2/out/schema_b.json` — skema hasil ekstraksi.
- `exp2/out/mapping_a.json`, `exp2/out/mapping_b.json` — output + parsed + usage.
- Baseline Exp-1: `evaluasi_exp1.md`, `hasil_client_a_v2.md`, `hasil_client_a_v2_run2.md`.