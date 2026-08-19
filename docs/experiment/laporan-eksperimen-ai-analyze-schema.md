# Laporan Eksperimen AI Analyze Schema

- **Periode:** eksperimen 1 s.d. 4 + lanjutan (Opsi 2, Opsi A+B, Opsi 2 lanjutan)
- **Status:** selesai (sebagai research spike / proof-of-feasibility)
- **Model utama:** Qwen2.5-3B-Instruct-Q4_K_M (CPU-only, llama.cpp)
- **Tujuan:** memvalidasi kemampuan dan desain sub-agent *AI Schema Analyzer* — sejauh mana Local LLM (3B) dapat memahami struktur database client yang beragam dan memetakannya ke konsep canonical, tanpa menyalin data bisnis ke AIOS Internal Database.

> Laporan ini merangkum hasil dari `evaluasi_exp1.md`, `evaluasi_exp2.md`,
> `evaluasi_exp3_hermes.md`, `evaluasi_exp4.md` (termasuk tiga lampirannya),
> dan `note_sumber.md`. Baca file-file tersebut untuk detail per eksperimen.

---

## 1. Konteks dan Pertanyaan Riset

AIOS harus beradaptasi dengan database client yang ada tanpa mengubahnya
(`CLIENT SYSTEM STAYS. AIOS ADAPTS.`). Salah satu komponen kuncinya adalah
**AI Schema Analyzer**: memahami skema client secara semantik dan memetakannya
ke **Canonical Data Model** (mis. `Product.name`, `Product.price`,
`Product.stock`).

Pertanyaan riset yang diuji berurutan:

1. Apakah Local LLM 3B mampu menganalisis skema secara mandiri (membaca file
   skema + menyimpulkan mapping)? (Exp-1)
2. Apakah membatasi peran LLM hanya pada *mapping* (ekstraksi struktur oleh
   kode) menaikkan keandalan? (Exp-2)
3. Apakah tool-calling loop (Hermes) dengan sampling terkontrol (`temp=0`)
   memperbaiki keandalan? (Exp-3)
4. Apakah pendekatan yang sama berlaku pada **database PostgreSQL nyata**
   dengan **boundary read-only** (metadata-only, 0 baris data)? (Exp-4)
5. Bagaimana menangani skema sulit (**EAV / Entity-Attribute-Value**) yang
   membuat mapping gagal, secara generik dan tanpa overfitting? (lanjutan)

---

## 2. Alur Eksperimen dari Awal sampai Akhir

### Tahap 0 — Dataset skema client (note_sumber.md)

Dibuat dua skema sample dengan arsitektur sangat berbeda:

| Skema | Arsitektur | Status sumber |
|---|---|---|
| Client A | Northwind (normalisasi klasik, kolom eksplisit) | `verified` — berdasar `pthom/northwind_psql` |
| Client B | EAV + JSONB (nama tersembunyi di baris atribut) | `modeling` — dibangun berdasar pola EAV, bukan DB produksi |

Client B sengaja dibuat karena menantang: nama `Product.name` tidak ada sebagai
kolom, melainkan sebagai *baris* pada tabel EAV (`attr_value_text`).

### Tahap 1 — Eksperimen 1: prompting saja (Qwen2.5-3B)

- Model membaca file SQL mentah sendiri + menyimpulkan mapping.
- Hasil: tidak andal. Run#1 → 2/3, run#2 (prompt identik) → 0/3 (regresi total,
  model mengartikan nama canonical sebagai nama kolom literal).
- Kesimpulan: prompting adalah faktor nyata (v2 > v1), tetapi **prompting saja
  tidak cukup** — keandalan 3B rendah untuk penalaran schema semantik.

### Tahap 2 — Eksperimen 2: ekstraksi deterministik + LLM hanya mapping

- `extractor.py` (kode) mem-parse file SQL → JSON skema deterministik.
- `mapper.py` → LLM hanya menerima skema JSON dan **menyarankan mapping** dengan
  format output kaku (`konsep/ditemukan/source/confidence/alasan`),
  `temperature=0`, `seed=42`.
- Hasil: **15/15 benar & deterministik** (Client A 6/6, Client B 9/9).
- Kesimpulan: membatasi peran LLM + menyuplai skema bersih dari kode
  **menaikkan keandalan secara nyata** dan menjadikan hasil deterministik.

### Tahap 3 — Eksperimen 3: Hermes tool-calling, sampling terkontrol

- Hermes v0.20.3 sebagai harness tool-calling (baca file + loop tool),
  `--temp 0 --seed 42` pada llama-server.
- Client A: **3/9** (1/3 per run, deterministik tetapi deterministik-*salah*).
- Client B: **loop degenerate** `search_files` untuk literal `"Product.name"`,
  tidak konvergen.
- Kesimpulan: kontrol sampling **bukan** faktor penentu; akar masalahnya adalah
  **jalur tool-calling bebas** yang membiarkan model mencari kolom secara
  literal dan masuk loop. Validasi pendekatan *on-rails* (Exp-2) sebagai
  keputusan desain yang benar.

### Tahap 4 — Eksperimen 4: PostgreSQL nyata, boundary read-only

Tiga varian diuji pada database PostgreSQL 18 nyata (`client_a_db`,
`client_b_db`), dengan role `aios_schema_reader` (LOGIN only, tanpa privilege
di tabel bisnis):

| Varian | Peran LLM | Hasil |
|---|---|---|
| A/B (`agent_query.py`) | menulis SQL katalog sendiri (agent loop) | **gagal** — SQL salah sintaks, loop query identik sampai MAX_ITER, lambat |
| C1 (`agent_tools.py`) | memilih alat katalog generik (list_tables, list_columns, list_foreign_keys) | **berbahaya** — halusinasi struktur yang tak pernah di-query (kolom `price`/`stock` fiktif, tipe salah) |
| C2 (`extractor_pg.py` + `mapper_pg.py`) | hanya usulan mapping dari skema hasil ekstraksi kode | **berhasil** — 15/15 (A 6/6, B 9/9), metadata-only, deterministik |

**Temuan boundary penting:** `information_schema` di PostgreSQL
menyembunyikan struktur dari user tanpa privilege (KOSONG); struktur hanya
terbaca via **`pg_catalog`**. Akses data (`SELECT/DELETE/UPDATE/INSERT/DROP`)
**ditolak server** — boundary teknis terbukti nyata, bukan sekadar filter teks
di kode. **0 baris data bisnis pernah terbaca** di semua varian.

### Tahap 5 — Lanjutan Opsi 2: perluasan extractor (schema + view)

- `extractor_pg.py` diperluas: semua schema user, `relkind IN ('r','v')`
  (tabel + view), output punya field `schema`/`kind`.
- Objek uji baru: view `public.product_catalog` dan schema non-`public`
  `app_schema.warehouse`.
- Hasil: 7 objek terbaca (tanpa regresi); view & schema non-`public` kini
  terlihat. **Temuan baru:** input v2 yang memuat `schema`/`kind`/prefix FK
  membuat `Product.price` Client B berubah menjadi `false` — bukti bahwa
  **format input LLM memengaruhi hasil mapping** pada kasus EAV sulit.

### Tahap 6 — Lanjutan Opsi A+B: perbandingan 3 format prompt (anti-overfitting)

- **Opsi A:** extractor tetap menghasilkan metadata lengkap untuk keperluan
  teknis, tetapi input ke LLM tidak boleh memuat info berulang yang tidak
  membantu.
- **Opsi B:** uji 3 format prompt (F1 ringkas, F2 lengkap, F3 ringkas +
  qualified) × 2 run per sel, pada **4 skema** (ditambah `client_c_db`
  relasional Indonesia dan `client_d_db` flat tanpa FK).
- Hasil: **semua sel 3/3 kecuali F2 di client_b** yang deterministik gagal
  `price` (2/2). F1 dan F3 identik dan paling stabil lintas 4 bentuk skema.
- Kesimpulan: format ringkas (F1/F3) = kandidat terbaik; tidak ada overfitting
  yang terbukti (skema baru dibuat setelah format dipilih konsepnya);
  batas "jangan mengarang" terjaga di client_d.

### Tahap 7 — Lanjutan Opsi 2: deteksi EAV generik + anotasi (A1/A2)

Menyelesaikan **akar masalah** price-di-EAV secara generik dan tetap
metadata-only:

- **Deteksi EAV deterministik** (`extractor_pg.detect_eav`), struktural:
  tabel nilai = PK komposit (≥2 kolom) yang semuanya FK + ≥1 kolom nilai;
  klaster = ≥2 tabel nilai berbagi 2 parent sama; tabel definisi = parent
  dengan varchar UNIQUE non-PK/FK. Output `eav_clusters` + `unique_columns`.
- **Dua bentuk anotasi** dibangun dari hasil deteksi: A1 (objek `eav` di dalam
  schema JSON), A2 (hint kalimat di prompt, di luar JSON).
- Skema uji ke-5: `client_e_db` (EAV Indonesia: `objek`,
  `definisi_atribut`, `nilai_teks/angka/tanggal`).

Hasil deteksi (verifikasi kode, tanpa LLM):

| Skema | Klaster EAV terdeteksi? | Tabel definisi / pembeda |
|---|---|---|
| client_a (Northwind) | tidak | — |
| client_b (EAV+JSONB) | ya | `attribute_definitions.attribute_code` |
| client_c (Indonesia) | tidak | — |
| client_d (flat) | tidak | — |
| client_e (EAV Indonesia) | ya | `definisi_atribut.kode_atribut` |

Matriks LLM (temp=0, seed=42, 2 run per sel):

| Sel | Hasil (name/price/stock) | Catatan |
|---|---|---|
| client_e F1+A0 (baseline) | 3/3, 3/3 | skema baru, kolom Indonesia |
| client_e F1+A1 | 3/3, 3/3 | |
| client_e F1+A2 | 3/3, 3/3 | source sertakan `definisi_atribut.kode_atribut` |
| client_b F1+A1 | 3/3, 3/3 | |
| client_b F1+A2 | 3/3, 3/3 | source sertakan `attribute_definitions.attribute_code` |
| **client_b F2+A2 (diagnostik)** | **3/3, 3/3** | F2 tanpa anotasi: price=false 2/2 |

**Temuan kunci:** sel diagnostik membuktikan akar masalah terselesaikan —
F2 yang deterministik gagal `price` (2/2) menjadi 3/3 begitu hint A2
ditambahkan; model kini menelusuri rantai `attr_value_num.attribute_id ->
attribute_definitions.attribute_code`. Deteksi EAV generik menyala di kedua
skema EAV (termasuk yang namanya beda total) dan tidak salah-positif di 3
skema non-EAV.

---

## 3. Ringkasan Hasil Lintas Eksperimen

| Aspek | Exp-1 (Hermes, bebas) | Exp-2 (extract + mapping, file SQL) | Exp-3 (Hermes, temp=0) | Exp-4 A/B (LLM tulis SQL) | Exp-4 C1 (LLM pilih alat) | Exp-4 C2 (extract nyata + mapping) |
|---|---|---|---|---|---|---|
| Sumber skema | file SQL mentah | file SQL (parser) | file SQL mentah | PostgreSQL nyata | PostgreSQL nyata | PostgreSQL nyata |
| Client A | 0–2/3 tak andal | 6/6 | 3/9 (1/3) | loop, 0 struktur | halusinasi | **6/6** |
| Client B (EAV) | 0/3 | 9/9 | loop, tidak konvergen | loop | (belum diuji) | **9/9** (conf sedang) |
| Data terpapar | — | sampel baris di input | — | tidak (ditolak) | tidak | **tidak (0 baris)** |
| Cepat | sedang | cepat | lambat | lambat (loop) | cepat | **cepat** |
| Deterministik | tidak | ya | ya (tetapi salah) | n/a (loop) | n/a | **ya** |

### Akhir rantai eksperimen (dengan anotasi):

- Format ringkas (F1) + anotasi A2 → benar di **5 skema** yang sangat berbeda
  arsitektur, deterministik 2/2 per sel.
- Sel diagnostik F2+A2 → format "bermasalah" pun terselamatkan oleh anotasi.

---

## 4. Temuan Kunci (Sintesis)

1. **Keandalan naik tajam ketika peran LLM dipersempit.** Membaca + menganalisis
   (Exp-1/3) → tidak andal; hanya *mapping* dari skema hasil kode (Exp-2/C2)
   → 15/15 deterministik. Peran yang dimenangkan adapter (kode), bukan LLM.

2. **Tool-calling loop pada model 3B berbahaya.** Bebas memilih tool (Hermes
   Exp-3) → loop degenerate; memilih alat eksplorasi (C1) → **halusinasi
   struktur** yang tak diperiksa (kolom karangan). Halusinasi lebih berbahaya
   daripada error karena output tampak meyakinkan.

3. **Boundary teknis metadata-only terbukti nyata.** `pg_catalog` terbaca,
   tabel data ditolak server. 0 baris data bisnis pernah terbaca. Desain
   keamanan "baca struktur, bukan data" adalah penghalang DB nyata, bukan
   komitmen teks.

4. **`information_schema` ≠ struktur universal.** PostgreSQL menyembunyikan
   katalog dari user tanpa privilege; harus pakai `pg_catalog`. Ini menghapus
   ilusi bahwa LLM bisa "menebak cara baca" lintas mesin tanpa panduan.

5. **Format input LLM memengaruhi hasil mapping.** Perubahan kecil (tambahan
   `schema`/`kind`/prefix FK) mengubah keputusan model pada kasus EAV sulit
   (B price: true → false). Format ringkas (F1/F3) paling stabil.

6. **Anotasi deterministik menyelesaikan kasus sulit.** Hint A2 (dibangun dari
   deteksi kode, bukan nama hardcoded) membuat model menelusuri rantai ke kode
   atribut pada skema EAV — akar masalah yang dihipotesiskan, terbukti lewat
   sel diagnostik F2+A2.

7. **Metadata-only menurunkan confidence pada kasus sulit (B: sedang)** — jujur
   dan selaras dengan use case C6 (low-confidence → penandaan + validasi
   client). Trade-off keamanan vs akurasi nyata, bukan teoritis.

8. **Anti-overfitting terjaga.** Deteksi diuji lintas 5 skema; format dipilih
   sebelum skema client_c/d dibuat; anotasi dibangun dari hasil deteksi aktual.

---

## 5. Keputusan Desain yang Divalidasi untuk Implementasi

Berdasarkan bukti eksperimen, desain sub-agent *AI Schema Analyzer* untuk
project AIOS:

1. **Database Adapter (kode)** mengekstrak struktur via katalog mesin
   (`pg_catalog` untuk PostgreSQL) sebagai role read-only per client.
2. **Ekstraksi deterministik** menghasilkan metadata skema + hasil deteksi pola
   struktural (mis. EAV: `eav_clusters`, `unique_columns`).
3. **Input ke LLM** memakai format **ringkas** (F1) + **anotasi A2** (hint dari
   hasil deteksi, di luar JSON).
4. **LLM hanya menyarankan mapping** ke konsep canonical (bukan menulis SQL,
   bukan memilih alat, bukan membaca file bebas), dengan format output kaku,
   `temperature=0`, `seed` tetap.
5. **Hasil + confidence disimpan di AIOS Internal Database** per tenant; klien
   memvalidasi mapping di UI (C6); low-confidence ditandai.
6. **Boundary teknis**: metadata-only, role DB read-only, server-lah yang
   menolak data — bukan filter teks di kode.

Yang **tidak** divalidasi oleh eksperimen ini (tetap terbuka): engine database
lain (MySQL/SQL Server/Oracle — perbedaan data dictionary), model LLM lebih
besar (7B+, kebijakan override per peran terbuka — ADR-004), re-adaptasi saat
skema berubah (C14), dan isolasi multi-tenant / metering token.

---

## 6. Referensi

### Referensi terdaftar di registry (docs/references/REFERENCES.md)

| REF-ID | Referensi | Relevansi pada eksperimen |
|---|---|---|
| REF-005 | Rahm & Bernstein, *A survey of approaches to automatic schema matching*, VLDB Journal 10(4), 2001 | Landasan klasik *schema matching* — memetakan struktur beragam ke model semantik |
| REF-008 | Sheetrit et al., *ReMatch: Retrieval Enhanced Schema Matching with LLMs*, arXiv 2024 | Pembanding: pendekatan LLM untuk schema matching |
| REF-013 | Gungor et al., *Schemora: schema matching via multi-stage recommendation and metadata enrichment using off-the-shelf LLMs*, arXiv 2025 | Pembanding: enrichment metadata untuk LLM schema matching |
| REF-014 | Wang et al., *LLMATCH: A Unified Schema Matching Framework with LLMs*, APWeb/arXiv 2025 | Pembanding: LLM sebagai basis framework schema matching |
| REF-015 | Seedat & Van Der Schaar, *Bootstrapping Self-Improvement of Language Model Programs for Zero-Shot Schema Matching*, ICML 2025 | Pembanding: zero-shot schema matching dengan LLM |
| REF-017 | PostgreSQL Documentation | Dasar perilaku `pg_catalog`, `information_schema`, privilege (temuan boundary) |

> Catatan: eksperimen ini berstatus *proof-of-feasibility*, bukan implementasi
> resmi. Referensi di atas mendukung arah desain; keputusan final dan ADR
> (format ringkas + anotasi, deteksi EAV, boundary role read-only) belum
> ditetapkan dan menunggu keputusan user.

### Referensi dataset eksperimen (note_sumber.md)

- **EAV / CR (Entity-Attribute-Value Model)** — Wikipedia
  https://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model
- **JSON Types — PostgreSQL Documentation**
  https://www.postgresql.org/docs/current/datatype-json.html
- **Northwind SQL — `pthom/northwind_psql`** (status: verified)
  https://github.com/pthom/northwind_psql

---

## 7. Data Pendukung (Lokasi File)

- `docs/experiment/note_sumber.md` — dataset & status verifikasi sumber.
- `docs/experiment/evaluasi_exp1.md` — Exp-1 (prompting saja).
- `docs/experiment/evaluasi_exp2.md` — Exp-2 (hibrida extract + mapping).
- `docs/experiment/evaluasi_exp3_hermes.md` — Exp-3 (Hermes, temp=0).
- `docs/experiment/evaluasi_exp4.md` — Exp-4 + lampiran Opsi 2, Opsi A+B,
  Opsi 2 lanjutan (deteksi EAV + anotasi).
- `docs/experiment/exp2/extractor.py`, `exp2/mapper.py`, `exp2/out/`.
- `docs/experiment/exp3/prompts/`, `exp3/out/`.
- `docs/experiment/exp4/agent_query.py` (varian A/B), `agent_tools.py`
  (varian C1), `extractor_pg.py` (ekstraksi + deteksi EAV), `mapper_pg.py`,
  `format_compare.py` (3 format), `eav_compare.py` (A1/A2), `hybrid_out/`.

---

## 8. Keterbatasan dan Batas Kejujuran

- Satu model (Qwen2.5-3B); hasil bisa berbeda di model lain.
- Satu mesin (PostgreSQL); perbedaan data dictionary mesin lain belum diuji.
- Skema uji buatan (5 skema), bukan database produksi; `client_b` dan
  `client_e` adalah *pemodelan* pola EAV, bukan snapshot DB riil.
- Mapping hanya diuji pada 3 konsep canonical (name/price/stock); generalisasi
  ke kosakata canonical lebih luas belum diuji.
- Deteksi EAV heuristik bisa salah-positif di bentuk skema yang tak diuji.
- Usulan mapping dari LLM tetap perlu **validasi client** (C6) — eksperimen
  membuktikan usulan akurat & deterministik, bukan substitusi konfirmasi klien.
- Tidak ada sumber yang dipalsukan; seluruh klaim status ada di tabel
  verifikasi `note_sumber.md`.