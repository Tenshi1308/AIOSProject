# Evaluasi Eksperimen 4 — Analyze Schema pada PostgreSQL Nyata (boundary read-only)

> **Lampiran (setelah spike selesai):**
> - Opsi 2 — perluasan extractor (schema + view), dan
> - Opsi A+B — perbandingan 3 format prompt input LLM (anti-overfitting).
> Lihat kedua "## Lampiran — ..." di akhir.

Eksperimen lanjutan dari Exp-1/2/3. Tujuan: menguji desain sub-agent Analyze
Schema **pada database nyata** (PostgreSQL 18 lokal), dengan dua konteks model:

1. Skema `client_a_db` (Northwind, normalisasi klasik — kolom jelas);
2. Skema `client_b_db` (EAV + JSONB — nama tersembunyi di baris atribut).

Keputusan desain yang diuji (hasil kesepakatan sebelum spike):

- **Metadata-only**: TIDAK ada satu baris data bisnis pun yang boleh terpapar.
- **Boundary teknis**: role DB khusus (`aios_schema_reader`, LOGIN only, tanpa
  privilege apa pun di tabel bisnis). Server-lah yang menolak akses data,
  bukan filter teks di kode.
- **Adaptasi di AI**: developer tidak menulis penerjemah/mapping per database.
  Yang diuji adalah sejauh mana Qwen2.5-3B mampu menentukan analisis sendiri.

Hipotesis yang diuji: "AI yang menentukan cara query struktur" pada model 3B
(dibanding pola Exp-2 yang on-rails).

## Metode

- Model: Qwen2.5-3B-Instruct-Q4_K_M, llama.cpp OpenAI-compatible di
  `127.0.0.1:8080`, `temperature=0`, `seed=42` (determinisme maksimum).
- Role DB: `aios_schema_reader` — `LOGIN`, `NOSUPERUSER`, **tanpa** `SELECT`
  di tabel `public` mana pun. Hanya katalog (`pg_catalog`) yang terbaca.
- Database: `client_a_db`, `client_b_db` (dibuat dari skema sample eksperimen).
- Tiga varian dibandingkan:
  - **A/B**: LLM menulis SQL katalog sendiri, satu query per turn (loop agent).
  - **C1**: LLM memilih di antara alat katalog generik: `list_tables`,
    `list_columns(table)`, `list_foreign_keys()`.
  - **C2**: ekstraksi struktur **deterministik oleh kode** (pola Exp-2) dari
    pg_catalog sebagai role `aios_schema_reader`, lalu **LLM hanya** usulan
    mapping ke `Product.name/price/stock` — tanpa baris sampel.

## Temuan Boundary (berlaku semua varian)

Verifikasi di PostgreSQL 18:

| Operasi | Hasil |
|---|---|
| `information_schema.tables` sebagai role tanpa privilege | **KOSONG** (privilege-filtered) |
| `pg_catalog.pg_tables` / `pg_attribute` | **TERBACA** (tidak difilter privilege) |
| `SELECT * FROM products` / `orders` | **DITOLAK** `permission denied` |
| `DELETE/UPDATE/INSERT/DROP` | **DITOLAK** `permission denied` / `must be owner` |

**Temuan penting**: `information_schema` di PostgreSQL menyembunyikan struktur
dari user tanpa privilege. Untuk membaca struktur kita harus pakai `pg_catalog`
(level lebih rendah). Ini fakta penting desain: "struktur bisa dibaca, data
mustahil" **terbukti nyata**, tetapi hanya via `pg_catalog`.

## Hasil per Varian

### Varian A/B — LLM menulis SQL sendiri (agent_query.py)

- Model mengeluarkan **beberapa blok JSON per respons** dan **baris baru mentah
  di dalam string SQL** → JSON tak valid; parser perlu diperbaiki agar adil.
- Query yang sah sekalipun **salah sintaks**:
  `pg_catalog.format_type(pg_catalog.atttypid, ...)` → kolom di-prefix schema
  (harusnya `a.atttypid`).
- **Loop**: model mengulang query IDENTIK sampai `MAX_ITER` (24 → 10), tidak
  pernah belajar dari error server.
- Biaya: puluhan menit per run (setiap turn pengiriman ulang seluruh context, LLM
  CPU lambat). Run client_b dihentikan user saat iterasi ke-7 (loop sama).

Kesimpulan A/B: **gagal** — 3B tidak andal menulis SQL katalog sendiri, tidak
self-correct, dan lambat.

### Varian C1 — LLM memilih alat katalog (agent_tools.py)

- Model memakai alat dengan benar (list_tables → 5 tabel, kolom categories,
  foreign keys) dan **selesai cepat** (5 iterasi, ~1-2 menit).
- **NAMUN**: pada FINAL, model **menghalusinasi (fabricate) struktur tabel yang
  TIDAK pernah ia query**:
  - `products.product_name` → benar (dari FK), tapi kolom `unit_price`,
    `units_in_stock` diganti menjadi `price`/`stock` (fiktif);
  - `orders`: `status` (tidak ada), `customer_id: integer` (salah tipe);
  - `suppliers`: `contact_email` (tidak ada).
- Akibat: mapping `Product.name` jadi `found:false, source:
  products.product_name, confidence sedang` — **padahal kolom benar ada**.

Kesimpulan C1: **hibrida dengan LLM-aktor tidak aman** — model mengisi celah
struktur yang tidak diperiksa dengan data karangan. Ini persis anti-pattern
yang dilarang AGENTS.md (`AIOS MUST NOT invent or fabricate`).

### Varian C2 — ekstraksi deterministik + LLM mapping (extractor_pg.py + mapper_pg.py)

**Ekstraksi** (kode, role `aios_schema_reader`, pg_catalog):
- client_a db: 5 tabel, semua kolom/tipe/PK/FK benar (dibanding file SQL asal).
- client_b db: 7 tabel, FK benar (EAV/attr → definisi & object, order_lines).
- Tidak ada query ke tabel data; output hanya metadata.

**Mapping** (LLM, temp=0, seed=42):

Client A (2 run), metadata-only:

| Konsep | Hasil (kedua run) | Ground truth |
|---|---|---|
| Product.name | true, `products.product_name`, tinggi | ✓ |
| Product.price | true, `products.unit_price`, tinggi | ✓ |
| Product.stock | true, `products.units_in_stock`, tinggi | ✓ |

→ **6/6**, deterministik, identik dengan Exp-2.

Client B (3 run), metadata-only:

| Konsep | Hasil (ketiga run) | Ground truth |
|---|---|---|
| Product.name | true, `attr_value_text` via objects/meta, **sedang** | ✓ nama di baris EAV |
| Product.price | true, `attr_value_num` via objects/meta, **sedang** | ✓ |
| Product.stock | true, `attr_value_num` via objects/meta, **sedang** | ✓ |

→ **9/9**, deterministik. Model mengenali representasi non-literal (EAV)
**tanpa contoh baris**, dengan confidence menurun ke `sedang` (jujur: tanpa
data, kedekatan representasi tidak bisa dikonfirmasi) → selaras C6
(low/mid-confidence → validasi client).

Usage: client A in=1360/out=183; client B in=1200/out=251 (deterministik antar
run, byte-identik output untuk B).

## Perbandingan Eksperimen 1-4

| Aspek | Exp-1 (Hermes, bebas) | Exp-2 (extract kode + LLM mapping, file SQL) | Exp-4 A/B (LLM tulis SQL) | Exp-4 C1 (LLM pilih alat) | Exp-4 C2 (extract nyata + mapping) |
|---|---|---|---|---|---|
| Sumber skema | file SQL mentah | file SQL (parser) | PostgreSQL nyata | PostgreSQL nyata | PostgreSQL nyata |
| A | 0-2/3 tak andal | 6/6 | loop, 0 struktur | halusinasi | **6/6** |
| B (EAV) | 0/3 | 9/9 | loop | (belum diuji) | **9/9** (conf sedang) |
| Data terpapar | — | sampel baris di input | tidak (ditolak) | tidak | **tidak (0 baris)** |
| Cepat | sedang | cepat | lambat (loop) | cepat | **cepat** |
| Deterministik | tidak | ya | n/a (loop) | n/a | **ya** |

## Temuan Kunci

1. **Boundary teknis terbukti**: struktur → katalog (pg_catalog), data → ditolak
   server. "Analyze schema baca struktur, bukan data" bukan komitmen teks, tapi
   penghalang DB nyata. **0 baris data bisnis pernah terbaca** di semua varian.
2. **`information_schema` ≠ struktur universal**: PostgreSQL menyembunyikan
   katalog dari user tanpa privilege. Desain "AI menentukan cara query"
   menghadapi fakta mesin (pg_catalog vs information_schema vs data dictionary
   mesin lain). Ini menghapus ilusi bahwa LLM bisa "menebak cara baca" tanpa
   panduan; faktanya, bahkan cara baca yang benar perlu diketahui.
3. **3B + penulisan SQL bebas (A/B): gagal** — loop tanpa self-correction,
   lambat. Konsisten dengan Exp-1/3.
4. **3B + pemilihan alat (C1): berbahaya secara semantik** — halusinasi struktur
   yang tak diperiksa (mengisi kolom karangan). Halusinasi ini **lebih berbahaya
   daripada error**, karena output tampak meyakinkan.
5. **3B + peran mapping saja (C2): andal & deterministik** — 15/15 usulan benar
   pada PostgreSQL nyata, metadata-only, cepat. Pola Exp-2 terkonfirmasi pada
   DB sungguhan dengan boundary keamanan.
6. **Metadata-only menurunkan confidence pada kasus sulit (B: sedang)** — jujur
   dan **selaras dengan C6** (low-confidence → penandaan + validasi client).
   Trade-off keamanan vs akurasi nyata, bukan teoritis.

## Keterbatasan

- Model tunggal (Qwen2.5-3B). Model lebih besar (7B+/JSON-tools native) belum
  diuji; temuannya spesifik kapasitas ini.
- Satu mesin (PostgreSQL). Perbedaan katalog MySQL/SQL Server/Oracle belum diuji.
- C1 hanya diuji pada client_a; pola halusinasinnya sudah cukup untuk verdict.
- Skala kecil (2 skema sample; client_a order_details tidak full karena data
  sample FK rusak di file SQL — tapi struktur tetap diuji dari katalog).

## Verdict untuk desain sub-agent Analyze Schema

| Pertanyaan | Jawaban berdasarkan bukti |
|---|---|
| "LLM tulis SQL sendiri di 3B" layak? | **Tidak** (loop, lambat, tidak self-correct). |
| "LLM pilih alat eksplorasi di 3B" aman? | **Tidak untuk struktur** (halusinasi data yang tak diperiksa). |
| "Ekstraksi deterministik + LLM mapping" terbukti? | **Ya** — 15/15 pada PostgreSQL nyata, metadata-only. |
| Boundary "baca struktur, bukan data" mungkin? | **Ya**, ditegakkan server (pg_catalog terbaca, tabel data ditolak). |
| Metadata-only cukup? | **Cukup untuk struktur**, dan confidence rendah → validasi client (C6). |

**Kesimpulan Exp-4**: arah "AI yang menentukan cara query" tidak realistis pada
model 3B; arah yang dijamin aman & andal adalah **ekstraksi struktur
deterministik oleh adapter (pg_catalog untuk PostgreSQL) + LLM hanya usulan
mapping + validasi client**, dengan boundary read-only sebagai penjaga "tidak
ada data terpapar". Ini konsisten penuh dengan keputusan desain (metadata-only,
boundary teknis, satu role per client) — hanya peran terperinci "siapa yang
menulis query" yang dimenangkan **adapter (kode)**, bukan LLM.

## Data pendukung

- `exp4/agent_query.py` — varian A/B (LLM tulis SQL; gagal/loop).
- `exp4/agent_tools.py` — varian C1 (LLM pilih alat; halusinasi).
- `exp4/extractor_pg.py` — ekstraksi deterministik pg_catalog.
- `exp4/mapper_pg.py` — LLM mapping metadata-only.
- `exp4/out/` — log varian A/B (snap + log).
- `exp4/hybrid_out/` — log C1, `schema_a.json`, `schema_b.json`,
  `mapping_a.json`, `mapping_b.json` (C2).

---

## Lampiran — Opsi 2: perluasan extractor (schema + view)

Disepakati user: (1) sertakan tabel+view (`relkind r,v`), (2) uji dengan objek
baru, (3) berhenti setelah dicatat. Tujuan: mengurangi kasus struktur yang
tersembunyi dari mekanisme baca standar (view, schema non-`public`).

### Perubahan extractor_pg.py

- `list_tables`: semua schema USER (bukan `pg_catalog`/`information_schema`/
  `pg_toast`), `relkind IN ('r','v')`, output `schema|relname|relkind`.
- `list_columns`: parameter schema + table.
- `list_foreign_keys`: sertakan nama schema di kedua sisi.
- Output tabel kini punya field `schema`, `kind`.

### Objek uji ditambahkan di `client_a_db`

- View `public.product_catalog` (relkind `v`) di atas `products`.
- Schema `app_schema` + tabel `app_schema.warehouse` (relkind `r`).

### Hasil ekstraksi

- `client_a_db`: 7 objek — `app_schema.warehouse` (r), 5 tabel public, dan
  `public.product_catalog` (v). FK tetap benar (tidak ada regresi).
- `client_b_db`: 7 tabel (semua `r`), FK tetap benar. Tidak ada regresi.
- Boundary tetap: semua dibaca dari pg_catalog sebagai `aios_schema_reader`,
  tanpa satu baris data pun.

### Hasil mapping (LLM, temp=0, seed=42)

- Client A (2 run): **6/6** benar, deterministik. Menarik: LLM memilih **view
  `product_catalog`** sebagai sumber (bukan tabel `products`) — tetap benar
  karena kolomnya berasal dari products.
- Client B (3 run): **berubah vs v1** — `Product.price` menjadi `false` (v1:
  `true` 3/3). Penyebab dugaan: input v2 menambah field `schema`/`kind` dan
  prefix `public.` pada FK, yang mengubah cara model menalar skema EAV.

### Temuan baru (penting)

1. **Perluasan extractor sukses** — view & schema non-`public` kini terlihat,
   tanpa regresi ekstraksi. Kelemahan "struktur tersembunyi" berkurang.
2. **Format input LLM memengaruhi hasil mapping** — perubahan kecil (tambahan
   `schema`/`kind`/prefix) mengubah keputusan model pada kasus EAV yang sulit
   (B price: true → false). Ini bukti lanjutan bahwa mapping 3B **sensitif
   terhadap tatanan input**, bukan hanya isi.
3. **Konsisten dengan C6**: output yang berubah/rendah-confidence inilah yang
   dirancang untuk **divalidasi client** — bukan dipercaya mentah.

### Status

Opsi 2 selesai dan dicatat. Tidak ada file arsitektur AIOS yang diubah; tidak
ada ADR; tidak ada commit. Lanjutan (desain sub-agent / pembahasan format input
mapping) menunggu keputusan user.

---

## Lampiran — Opsi B: bandingkan 3 format prompt (anti-overfitting)

Keputusan user (menyusul Opsi A — pisahkan metadata dari input LLM):
- **Opsi A**: extractor tetap menghasilkan metadata lengkap (`schema`/`kind`/
  prefix) untuk keperluan teknis, tetapi input ke LLM **tidak boleh** memuat
  info berulang yang tidak membantu.
- **Opsi B**: uji beberapa format prompt, pilih yang paling stabil — **jangan
  overfitting** ke contoh uji. Hasil harus nyata, ini masih eksperimen.
- Format yang diuji: **3** (F1 ringkas, F2 lengkap, F3 ringkas+qualified).
- Run per sel: **2** (temp=0, seed=42). Database uji diperluas ke **4 skema**.

### Format yang dibandingkan (isi sama, bentuk beda)

| Format | `schema`/`kind` di tabel | Prefix schema di FK |
|---|---|---|
| F1 Ringkas | tidak | tidak |
| F2 Lengkap | ya | ya (selalu) |
| F3 Ringkas + qualified | tidak | ya, hanya jika >1 schema |

### Skema uji baru (anti-overfitting)

Dibuat `client_c_db` & `client_d_db` di PostgreSQL (CONNECT saja untuk
`aios_schema_reader`):

- **client_c_db** — relasional berbahasa Indonesia: `barang (kode, nama,
  harga_jual, stok_tersedia)`, `penjualan`, `detail_penjualan` (3 FK).
  Menguji adaptasi penamaan non-Inggris. Ground truth: `barang.nama`,
  `barang.harga_jual`, `barang.stok_tersedia`.
- **client_d_db** — datar & minim: satu tabel `tbl_a (rec_id, nama_barang,
  harga, qty_stok)`, tanpa FK. Menguji batas "jangan mengarang" saat struktur
  sangat sederhana. Ground truth: `tbl_a.nama_barang`, `tbl_a.harga`,
  `tbl_a.qty_stok`.

### Hasil (benar = sesuai ground truth; 2 run per sel)

| Skema | F1 | F2 | F3 |
|---|---|---|---|
| client_a (Northwind, 7 objek) | 3/3, 3/3 | 3/3, 3/3 | 3/3, 3/3 |
| client_b (EAV+JSONB, 7 tabel) | 3/3, 3/3 | **price=false**, **price=false** | 3/3, 3/3 |
| client_c (Indonesia, 3 tabel) | 3/3, 3/3 | 3/3, 3/3 | 3/3, 3/3 |
| client_d (flat, 1 tabel) | 3/3, 3/3 | 3/3, 3/3 | 3/3, 3/3 |

Semua sel 3/3 kecuali **F2 di client_b** yang deterministik gagal `price`
(dua run sama). F1 dan F3 identik di semua skema (tidak pernah beda).

### Temuan Opsi B (penting)

1. **Dugaan Opsi 2 terkonfirmasi secara terkontrol**: format "lengkap" (F2,
   dengan `schema`/`kind`/prefix) yang gagal di client_b `price`, sementara
   format ringkas (F1/F3) dengan **isi yang sama persis** berhasil. Karena
   isi skema identik, yang mengubah hasil hanyalah **bentuk tampilan input**.
2. **F1 / F3 setara dan paling stabil**: benar di semua 4 bentuk skema (klasik
   Inggris, EAV+JSONB, Indonesia relasional, flat tanpa FK), deterministik
   2/2. Ini menandai format ringkas sebagai kandidat terbaik.
3. **Tidak ada overfitting yang terbukti**: format ringkas sukses melintasi
   pola skema yang beragam, termasuk yang baru dibuat setelah format dipilih
   konsepnya (client_c, client_d). Kelemahan potensial (format terbaik hanya
   terbukti pada 4 skema ini) dicatat sebagai keterbatasan, bukan klaim final.
4. **Batas "jangan mengarang" terjaga**: client_d (hanya `nama_barang`,
   `harga`, `qty_stok`) dipetakan ke kolom yang benar-benar ada, tidak ada
   kolom karangan. Konsisten dengan anti-halusinasi varian C1.

### Status

Opsi A + B selesai dan dicatat. Tidak ada perubahan arsitektur AIOS; tidak ada
ADR; tidak ada commit. `format_compare.py` (render 3 format + runner) tersimpan
di `exp4/` untuk dipakai ulang jika perlu. Lanjutan (mis. menetapkan format
ringkas sebagai standar input LLM, atau uji skema lebih banyak) menunggu
keputusan user.