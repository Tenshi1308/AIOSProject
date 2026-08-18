# Catatan Sumber — Dataset Eksperimen Skema Client

Eksperimen ini adalah **research spike / proof-of-feasibility** untuk
memvalidasi kemampuan Local LLM (Qwen2.5-3B, CPU-only) dalam **analisis
skema semantik** pada skema client yang sangat berbeda secara
arsitektural. **Ini BUKAN implementasi resmi fase #11** dan **BUKAN**
implementasi use case C5 / Data Access Agent.

Hasil eksperimen ini menjadi **patokan** untuk fase implementasi nanti.

## Status Verifikasi Sumber

| Skema | Status | Keterangan |
|---|---|---|
| Client A (Northwind) | `verified` (⚡) | Berdasar skema database riil `pthom/northwind_psql` yang sudah diverifikasi |
| Client B (EAV + JSONB) | `modeling` | Dibangun **berdasar pola** (bukan salinan literal DB produksi); lihat referensi di bawah |

> Penting: Client B **bukan** salinan database produksi yang riil. Ia
> adalah **pemodelan** arsitektur EAV + JSONB berdasarkan sumber yang
> tercantum di bawah, dibuat untuk menguji kemampuan model memahami
> 'nama' yang disembunyikan di baris EAV (`attr_value_text`).

## Referensi

### EAV (Entity-Attribute-Value)

- **EAV / CR (Entity-Attribute-Value Model)** — Wikipedia.
  "An entity–attribute–value (EAV) model ... is appropriate when the
  number of attributes (properties, parameters) that can be used to
  describe a thing (an 'entity' or 'object') is potentially very large,
  but the number that will actually apply to a given entity is
  comparatively modest."
  https://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model

- Note: halaman wiki menyebutkan properti umumnya disimpan sebagai
  **baris** pada tabel terpisah, sering dengan kolom bernilai kecil
  (bool/int/float/string) untuk menghindari pemborosan tipe data.

### JSONB (PostgreSQL)

- **JSON Types — PostgreSQL Documentation**.
  "The jsonb data type ... stores an efficient, binary representation of
  JSON ... which is by default not stored in a sorted order."
  https://www.postgresql.org/docs/current/datatype-json.html

- `->`, `->>`, `@>`, `?` operator serta indeks GIN untuk `jsonb`
  didokumentasikan pada halaman yang sama.

### Northwind (Client A)

- **Northwind SQL** — `pthom/northwind_psql` (PostgreSQL port dari
  Northwind klasik). Skema ini adalah database contoh bisnis yang umum
  (customers, orders, products, suppliers, order_details).
  https://github.com/pthom/northwind_psql

- Status: **verified (⚡)** — skema diambil dari sumber di atas.

## Batas Kejujuran

- Client B (`client_b_eav_jsonb.sql`) adalah **pemodelan pola**, bukan
  snapshot database produksi. Ini disengaja dan ditandai terekplicit.
- Sampel data pada kedua file bertujuan kecil (beberapa baris/tabel),
  cukup untuk validasi konsep, bukan simulasi volume data nyata.
- Tidak ada sumber yang dipalsukan; seluruh klaim status di atas
  tercantum di tabel verifikasi.