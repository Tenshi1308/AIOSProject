# Fase B — Prompt Evaluasi AI Schema Analyzer

Eksperimen research spike: menguji kemampuan Local LLM
(Qwen2.5-3B-Instruct-Q4_K_M, CPU-only) dalam **analisis skema semantik**
pada skema client yang sangat berbeda. Hermes (v0.20.3) hanya **alat
validasi**, bukan bagian stack AIOS.

## Canonical Model Minimal (Fase B-1)

Berdasar kesepakatan: fokus pada konsep yang ada di kedua client dengan
representasi sangat berbeda.

| Konsep canonical | Tipe | Ketersediaan |
|---|---|---|
| `Product.name` | string | wajib cari — dapat tersembunyi (mis. di baris EAV) |
| `Product.price` | number | opsional |
| `Product.stock` | number | opsional |

Prinsip: AIOS MUST NOT invent data yang tidak tersedia. Jika konsep tidak
ketemu, model harus menyatakan TIDAK TERSEDIA, jangan menebak.

## Metode Eksekusi (Fase B-2/B-3)

- Cara: **file tool** (keputusan user, rekomendasi) — prompt berisi
  canonical model + instruksi; Hermes membaca file skema SQL lewat tool
  `file`, lalu menganalisis. (Merepresentasikan Schema Analyzer yang
  diberi akses sumber data; prompt tetap pendek.)
- Toolset Hermes: `cli: [terminal, file]` (konfigurasi aktif).
- Eksekusi one-shot: `hermes -z "<prompt>"`.
- Approval tool dilewati untuk non-interaktif.

## Prompt Evaluasi Standar

Digunakan dua kali (Client A `client_a_northwind.sql`, Client B
`client_b_eav_jsonb.sql`), berbeda hanya pada path file.

```
Anda adalah AI Schema Analyzer untuk platform AIOS yang beradaptasi pada
database client yang beragam.

LANGKAH:
1. Gunakan tool [file] untuk MEMBACA isi lengkap file skema: <PATH_FILE_SQL>
2. Analisis skema secara SEMANTIK (bukan hanya nama kolom). Perhatikan
   tabel, kolom, tipe data, relasi, constraints, dan sampel data.
3. Petakan konsep yang tersedia ke Canonical Model berikut:
     - Product.name  (string)  - Wajib carikan, bisa tersembunyi
     - Product.price (number)  - Opsional
     - Product.stock (number)  - Opsional
4. Untuk SETIAP konsep canonical di atas, keluarkan:
     - Ditemukan atau TIDAK TERSEDIA
     - Sumber (tabel.kolom atau bagaimana data direpresentasikan)
     - Confidence (tinggi / sedang / rendah) + alasan singkat
5. JANGAN memfabrikasi. Jika suatu konsep tidak dapat dipastikan dari
   skema, nyatakan TIDAK TERSEDIA atau beri confidence rendah.
6. Selain Product, jika terlihat konsep lain yang jelas (mis. Order,
   Customer, Supplier), beri daftar singkat sebagai informasi tambahan.

Sajikan jawaban sebagai ringkasan terstruktur (bukan spekulasi naratif
panjang).
```

## Kriteria Evaluasi (Fase B-4)

Berdasar REQUIREMENTS.md DS-04 s.d. DS-08:

- **DS-04** — model menganalisis secara semantik, bukan hanya nama kolom.
  Bukti: mengenali 'nama produk' meski tersembunyi di baris EAV (Client B).
- **DS-05** — mempertimbangkan tables, columns, data types, relationships,
  constraints, sample values, naming patterns, semantic meaning.
- **DS-06** — memetakan pemahaman ke canonical model (semantic mapping).
- **DS-07** — representasi ternormalisasi (bekerja dengan konsep, bukan
  nama tabel/kolom client spesifik).
- **DS-08** — konsep setara dari client berbeda (Client A `products.
  product_name` vs Client B `attr_value_text 'Teh Botol'`) dipetakan ke
  konsep canonical yang sama (`Product.name`).

Skala hasil per konsep canonical: `ditemukan benar` / `ditemukan tapi
source kurang tepat` / `tidak ditemukan padahal ada` / `menebak/fabrikasi` /
`TIDAK TERSEDIA (benar)`.