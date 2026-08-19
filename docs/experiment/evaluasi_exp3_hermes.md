# Evaluasi Eksperimen 3 — AI Schema Analyzer via Hermes (Qwen2.5-3B, sampling terkontrol)

Eksperimen lanjutan setelah Exp-1 (Hermes, sampling tak terkontrol) dan
Exp-2 (hibrida: extractor deterministik + LLM mapping on-rails via API).

Tujuan Exp-3: memakai **Hermes sebagai harness tool-calling** untuk task
yang sama (baca file skema → mapping ke canonical), TAPI dengan variabel
**sampling dikendalikan** (`--temp 0 --seed 42` pada llama-server), untuk
mengisolasi pertanyaan:

> Apakah Hermes (tool-calling loop + `file` tool) + Qwen2.5-3B andal
> melakukan semantic schema analysis bila non-determinisme sampling
> sudah ditiadakan?

## Metode

- Model: Qwen2.5-3B-Instruct-Q4_K_M (CPU-only, llama.cpp).
- **Sampling dikontrol**: llama-server distart ulang dengan `--temp 0
  --seed 42` (ditambahkan ke `ai/start-aios-ai.ps1`). `mapper.py` Exp-2
  tak terpengaruh (ia mengirim `temperature`/`seed` per request).
- Harness: **Hermes v0.20.3**, mode one-shot `hermes -z "<prompt>"
  --yolo --in docs --usage-file <out.json>`.
  - CWD = `docs/` (SQL di bawah `docs/experiment/` ada di workspace,
    jadi `read` tak butuh approval; dan tidak ada AGENTS.md di `docs/`).
  - Prompt: instruksi rigid (baca file → analisis semantik → blok
    `konsep/ditemukan/source/confidence/alasan`), anti-ragu,
    anti-fabrikasi. Prompt di `exp3/prompts/prompt_hermes_{a,b}.txt`.
- Client A (Northwind): 3 run. Client B (EAV+JSONB): 1 run (lihat hasil —
    berhenti karena loop tak konvergen).
- Model disuruh MEMBACA file SQL (tidak diberi JSON hasil ekstraksi),
    dan bebas memakai tool (read/search) — ini yang membedakan dari Exp-2
    yang memberi skema JSON jadi.

## Hasil

### Client A (Northwind, kolom jelas) — 3 run identik

| Run | Product.name | Product.price | Product.stock | Skor |
|---|---|---|---|---|
| 1 | ditemukan: true (`products.product_name`) ✓ | false ✗ | false ✗ | 1/3 |
| 2 | true (`products.product_name`) ✓ | false ✗ | false ✗ | 1/3 |
| 3 | true (`products.product_name`) ✓ | false ✗ | false ✗ | 1/3 |

→ **3/9 konsep benar** (1/3 per run), **deterministik** (hasil sama
lintas run pada `temp=0`).

Ground truth: `Product.name`=`products.product_name` (ada, ✓),
`Product.price`=`products.unit_price` (ada, salah `false`),
`Product.stock`=`products.units_in_stock` (ada, salah `false`).

### Client B (EAV+JSONB) — run 1 TIDAK KONVERGEN

Model membaca file (isi penuh ke konteks), lalu **masuk loop degenerate**:
memanggil `search_files` untuk literal `"Product.name"` berulang kali
(14 pesan tool pada contoh transkrip, mayoritas `total_count: 0`), tetap
menerbitkan panggilan yang sama; Hermes mengeluarkan peringatan loop
(`idempotent_no_progress_warning`). Tidak ada jawaban mapping yang dicapai
dalam batas waktu eksekusi. Output kosong; usage tidak tercatat (process
dihentikan).

Karena `temp=0` bersifat deterministik, run B 2–3 dipastikan akan mengulang
loop yang sama dan tidak menambah informasi; tidak divalidasi ulang.

## Usage (Client A, per run)

- input 2594 / output 437 / total 26615 (cache_read 23584), `api_calls` 4.
- (Client B tidak tercatat — process dihentikan sebelum `--usage-file`
  menulis.)

## Perbandingan tiga eksperimen

| Aspek | Exp-1 (Hermes, default) | Exp-2 (hibrida on-rails) | Exp-3 (Hermes, temp=0) |
|---|---|---|---|
| Peran model | baca file + analisis + konklusi | hanya usulan mapping (skema JSON dari kode) | baca file + tool loop + konklusi |
| Kontrol sampling | tidak (temp 0.8) | ya (temp 0, seed) | ya (temp 0, seed) |
| Client A | 2/3 lalu 0/3 | 6/6 | **3/9** (1/3) |
| Client B (EAV) | 0/3 | 9/9 | **loop, tidak konvergen** |
| Deterministis | tidak | ya | ya (tetapi deterministik *salah*) |

## Temuan Kunci

1. **Kontrol sampling BUKAN faktor penentu kegagalan.** Dengan `temp=0`
   (deterministik), Hermes+3B tetap salah pada Client A (1/3) — dan justru
   menunjukkan kegagalan itu **stabil/berulang**. Keterlambatan Exp-1 bukan
   karena sampling acak semata.

2. **Masalahnya adalah tatanan/lingkungan tool-calling, bukan kapasitas
   model murni.** Model membaca skema ke konteks, tetapi **mengartikan nama
   canonical sebagai nama kolom literal** dan memanggil `search_files`
   untuk `"Product.name"` / `"Product.price"` / `"Product.stock"` (0 hasil),
   alih-alih memaknai `product_name` / `unit_price` / `units_in_stock`
   dari isi yang sudah dibacanya. Ini pola yang sama dengan Exp-1 run#2.

3. **Loop tool yang tidak produktif (Client B).** Pada skema EAV yang lebih
   luas, model tersangkut dalam loop `search_files` yang identik dan tidak
   mencapai jawaban — poin kuat bahwa **agent loop 3B dengan tool bebas
   tidak andal** untuk task penalaran skema semantik.

4. **Kontras menentukan dengan Exp-2.** Ketika model menerima skema hasil
   ekstraksi kode (JSON) dan HANYA diminta menyarankan mapping (tanpa
   tool bebas untuk disalahgunakan), ia benar **15/15 deterministik**
   (A 6/6, B 9/9). Perbedaan tunggal yang relevan: **model dipaksa
   "on-rails"** sehingga tidak memilih jalur tool yang keliru.

## Verdict untuk fase #11

| Pertanyaan | Jawaban berbasis bukti |
|---|---|
| Hermes + 3B (file-tool) andal untuk AI Schema Analyzer? | **Tidak** — salah persist di A (1/3) & loop di B, walau `temp=0`. |
| Apakah SERVAS mengubahnya? | **Tidak signifikan** — deterministik tetapi deterministik-salah / loop. |
| Pendekatan yang disarankan? | **Non-rail (kode ekstraksi + LLM mapping) seperti Exp-2** — andal & deterministik. Model TIDAK diberi tool bebas untuk menebak sumber kolom; kode yang menyusun skema. |
| Peran Hermes/agent? | Untuk skenario analisis skema, hindari memberi 3B tool `search` bebas; atau pakai model lebih mampu + batasi tool & loop. |

**Kesimpulan**: memperbaiki sampling (`temp=0`) tidak memperbaiki
keandalan AI Schema Analyzer bermodal 3B; akar masalah adalah **jalur
tool-calling bebas** yang membiarkan model mencari kolom secara literal dan
masuk loop. Validasi bahwa pendekatan **on-rails (extractor kode → LLM
mapping)** — hasil Exp-2 — adalah keputusan desain yang benar untuk fase
#11.

## Keterbatasan

- Hanya 1 model (Qwen2.5-3B) dan 3 run Client A + 1 run Client B (run B
  tidak konvergen; run B 2–3 dilewati karena loop deterministik — transkrip
  berisi bukti pengulangan identik).
- Hermes `-z` headless: Client A butuh `--in docs` (file di-workspace)
  agar `read` tidak butuh approval; dari CWD lain, path absolut `F:\`
  memicu stall (lihat catatan eksekusi).
- Output Hermes terkena artefak encoding (mis. `ĥalo` dari `halo`) saat
  redirect; tidak memengaruhi substansi jawaban.
- Loop B dihentikan oleh tool (timeout), bukan kesimpulan natural — status
  "tidak konvergen" diambil dari transkrip (buffer tool berulang) + timeout.

## Data pendukung

- `exp3/prompts/prompt_hermes_a.txt`, `prompt_hermes_b.txt` — prompt.
- `exp3/out/hasil_a_run{1,2,3}.txt` — output verbatim Client A.
- `exp3/out/usage_a_run{1,2,3}.json` — usage Client A.
- Client B: transkrip sesi Hermes (sesi terakhir, 15 pesan tool, loop
  `search_files`); tidak ada output file (`hasil_b_run1.txt` kosong, dibuang).
- Pembanding: `evaluasi_exp1.md` (Exp-1), `evaluasi_exp2.md` (Exp-2).
- Perubahan harness: `ai/start-aios-ai.ps1` (tambah `--temp 0 --seed 42`).